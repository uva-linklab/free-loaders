#include <stdbool.h>
#include <stdio.h>
#include <string.h>

#include <assert.h>

#include <libopenthread/platform/openthread-system.h>
#include <libopenthread/platform/plat.h>
#include <openthread/dataset_ftd.h>
#include <openthread/instance.h>
#include <openthread/ip6.h>
#include <openthread/platform/alarm-milli.h>
#include <openthread/tasklet.h>
#include <openthread/thread.h>
#include <openthread/udp.h>

#include <libtock-sync/services/alarm.h>
#include <libtock/interface/button.h>
#include <libtock/kernel/ipc.h>
#include <libtock/services/alarm.h>
#include <libtock/tock.h>

#include "acls.h"
#include "acls-config.h"
#include "svm.h"

// helper utility demonstrating network config setup
static void setNetworkConfiguration(otInstance* aInstance);

static otUdpSocket sUdpSocket;

void initUdp(otInstance* aInstance);

void handleUdpRecvTemperature(void* aContext, otMessage* aMessage,
                              const otMessageInfo* aMessageInfo);

void sendUdpTemperature(otInstance* aInstance, uint8_t temperature);

void send_tpm_packet(otInstance* ot);

// callback for Thread state change events
static void stateChangeCallback(uint32_t flags, void* context);

bool _g_ready = false;
uint32_t _g_last_pressed_debounce_ms = 0;
void button_press_cb(returncode_t rtc,
					 int button_no,
					 bool pressed);

// helper utility to print ip address
static void print_ip_addr(otInstance* instance);

otInstance* _g_instance = NULL;

uint16_t AUDIO_SAMPLES[ACLS_SAMPLE_LEN];

int main(__attribute__((unused)) int argc, __attribute__((unused)) char* argv[]) {
	/* float scaler[] = { */
	/* 	+0000.0643, +0000.0577, */
	/* 	+0000.0184, +0000.0233, */
	/* 	+1450.0000, +0596.0000, */
	/* 	+0119.0000, +0203.0000, */
	/* 	+1170.0000, +0280.0000, */
	/* 	+0065.7000, +0120.0000, */
	/* 	-0020.4000, +0149.0000, */
	/* 	+0071.4000, +0047.1000, */
	/* 	-0017.0000, +0036.3000, */
	/* 	+0013.3000, +0020.0000, */
	/* 	-0002.5800, +0018.3000, */
	/* 	+0009.0300, +0015.2000, */
	/* 	-0002.9300, +0013.4000, */
	/* 	+0005.2900, +0010.8000 */
	/* }; */

	/* float features[] = { */
	/* 	0.034, */
	/* 	0.017, */
	/* 	2388.572, */
	/* 	9.927, */
	/* 	1593.426, */
	/* 	0.158, */
	/* 	46.788, */
	/* 	24.624, */
	/* 	-1.867, */
	/* 	1.686, */
	/* 	8.638, */
	/* 	8.193, */
	/* 	-3.110, */
	/* 	8.174, */
	/* 	-5.257, */
	/* 	10.829, */
	/* 	3.186, */
	/* 	9.704, */
	/* 	-10.545, */
	/* 	52.661, */
	/* 	1.199, */
	/* 	1.398, */
	/* 	1.354, */
	/* 	0.045, */
	/* 	0.679, */
	/* 	0.242, */
	/* 	1.552, */
	/* 	0.991, */
	/* 	3.759, */
	/* 	0.412, */
	/* 	0.268, */
	/* 	0.160 */
	/* }; */

	/* // Scale the features. */
	/* for (uint8_t i = 0; i < sizeof(scaler) / sizeof(float) / 2; i++) */
	/* { */
	/* 	features[i] = (features[i] - scaler[2*i]) / scaler[2*i+1]; */
	/* } */

	/* int prediction = predict(features); */
	/* printf("prediction: %d\n", prediction); */

	// Initialize OpenThread instance.
	otSysInit(argc, argv);
	otInstance* instance;
	instance = otInstanceInitSingle();
	_g_instance = instance;
	assert(instance);

	// set child timeout to 60 seconds.
	otThreadSetChildTimeout(instance, 60);

	// Set callback to be notified when thread state changes.
	otSetStateChangedCallback(instance, stateChangeCallback, instance);

	///////////////////////////////////////////////////
	// THREAD NETWORK SETUP HERE

	// Configure network.
	setNetworkConfiguration(instance);

	// Init UDP interface.
	initUdp(instance);

	// Enable network interface.
	while (otIp6SetEnabled(instance, true) != OT_ERROR_NONE) {
		printf("Failed to start Thread network interface!\n");
		libtocksync_alarm_delay_ms(100);
	}

	// Print IPv6 address.
	print_ip_addr(instance);

	// Start Thread network.
	while (otThreadSetEnabled(instance, true) != OT_ERROR_NONE) {
		printf("Failed to start Thread stack!\n");
		libtocksync_alarm_delay_ms(100);
	}

	// Set up button callback.
	libtock_button_notify_on_press(0, button_press_cb);

	//
	////////////////////////////////////////////////////

	// OpenThread main loop.
	bool done_once = false;
	for (;;) {
		// Execute any pending OpenThread related work.
		otTaskletsProcess(instance);

		// Execute any platform related work (e.g. check
		// radio buffer for new packets).
		otSysProcessDrivers(instance);

		// If there is not pending platform or OpenThread
		// related work -- yield.
		if (!otTaskletsArePending(instance) &&
			!openthread_platform_pending_work()) {
			yield();
			/* send_tpm_packet(instance); */
			if (_g_ready && !done_once)
				capture();
		}

	}

	return 0;
}

// Helper method that configures the OpenThread network dataset
// for the desired tutorial configuration.
// We set the following dataset parameters:
//  -- Channel:    26
//  -- PanId:      0xabcd
//  -- Networkkey: 00112233445566778899aabbccddeeff
void setNetworkConfiguration(otInstance* aInstance) {
	otOperationalDataset aDataset;

	memset(&aDataset, 0, sizeof(otOperationalDataset));

	/* Set Channel to 26 */
	aDataset.mChannel = 26;
	aDataset.mComponents.mIsChannelPresent = true;

	/* Set Pan ID to abcd */
	aDataset.mPanId = (otPanId)0xabcd;
	aDataset.mComponents.mIsPanIdPresent = true;

	/* Set network key to 00112233445566778899aabbccddeeff */
	uint8_t key[OT_NETWORK_KEY_SIZE] = {
		0x00, 0x11, 0x22, 0x33,
		0x44, 0x55, 0x66, 0x77,
		0x88, 0x99, 0xaa, 0xbb,
		0xcc, 0xdd, 0xee, 0xff
	};
	memcpy(aDataset.mNetworkKey.m8, key, sizeof(aDataset.mNetworkKey));
	aDataset.mComponents.mIsNetworkKeyPresent = true;

	otError error = otDatasetSetActive(aInstance, &aDataset);
	assert(error == 0);

}

// Helper method that registers a stateChangeCallback to print
// when state changes occur (useful for debugging).
static void stateChangeCallback(uint32_t flags, void* context) {
	otInstance* instance = (otInstance*)context;
	if (!(flags & OT_CHANGED_THREAD_ROLE)) {
		return;
	}

	switch (otThreadGetDeviceRole(instance)) {
    case OT_DEVICE_ROLE_DISABLED:
		printf("[State Change] - Disabled.\n");
		break;
    case OT_DEVICE_ROLE_DETACHED:
		printf("[State Change] - Detached.\n");
		break;
    case OT_DEVICE_ROLE_CHILD:
		printf("[State Change] - Child.\n");
		printf("Successfully attached to Thread network as a child.\n");
		_g_ready = true;
		break;
    case OT_DEVICE_ROLE_ROUTER:
		printf("[State Change] - Router.\n");
		break;
    case OT_DEVICE_ROLE_LEADER:
		printf("[State Change] - Leader.\n");
		break;
    default:
		break;
	}
}

void button_press_cb(__attribute__ ((unused)) returncode_t rtc,
					 __attribute__ ((unused)) int button_no,
					 bool pressed)
{
	if (!_g_ready) { return; }

	printf("Button event.\n");

	if (!pressed) { return; }

	printf("Button pressed.\n");

	uint32_t now;
	uint32_t now_ms;
	libtock_alarm_command_read(&now);
	now_ms = libtock_alarm_ticks_to_ms(now);

	uint32_t d_last_pressed_ms = now_ms -_g_last_pressed_debounce_ms;
	if (d_last_pressed_ms < 300) { return; }
	_g_last_pressed_debounce_ms = now_ms;

	otInstance* const ot = _g_instance;

	if (!_g_ready)
	{
		printf("Not ready yet.\n");
		return;
	}

	printf("Sending packet.\n");

	send_tpm_packet(ot);

	return;
}

// Helper method to print the given Thread node's registered
// ipv6 address.
static void print_ip_addr(otInstance* instance) {
	char addr_string[64];
	const otNetifAddress* unicastAddrs = otIp6GetUnicastAddresses(instance);

	printf("[THREAD] Device IPv6 Addresses: ");
	for (const otNetifAddress* addr = unicastAddrs; addr; addr = addr->mNext) {
		const otIp6Address ip6_addr = addr->mAddress;
		otIp6AddressToString(&ip6_addr, addr_string, sizeof(addr_string));
		printf("%s\n", addr_string);
	}
}


void handleUdpRecvTemperature(void* aContext, otMessage* aMessage,
                              const otMessageInfo* aMessageInfo) {
	OT_UNUSED_VARIABLE(aContext);
	OT_UNUSED_VARIABLE(aMessageInfo);
	char buf[2];

	const otIp6Address sender_addr = aMessageInfo->mPeerAddr;
	otIp6AddressToString(&sender_addr, buf, sizeof(buf));

	otMessageRead(aMessage, otMessageGetOffset(aMessage), buf, sizeof(buf) - 1);
	printf("Received UDP Packet: %d\r\n", buf[0]);
}

void initUdp(otInstance* aInstance) {
	otSockAddr listenSockAddr;

	memset(&sUdpSocket, 0, sizeof(sUdpSocket));
	memset(&listenSockAddr, 0, sizeof(listenSockAddr));

	listenSockAddr.mPort = 1212;

	otUdpOpen(aInstance, &sUdpSocket, handleUdpRecvTemperature, aInstance);
	otUdpBind(aInstance, &sUdpSocket, &listenSockAddr, OT_NETIF_THREAD);
}

void sendUdpTemperature(otInstance* aInstance, uint8_t temperature) {

	otError error = OT_ERROR_NONE;
	otMessage*   message;
	otMessageInfo messageInfo;
	otIp6Address destinationAddr;

	memset(&messageInfo, 0, sizeof(messageInfo));

	otIp6AddressFromString("ff02::02", &destinationAddr);
	messageInfo.mPeerAddr = destinationAddr;
	messageInfo.mPeerPort = 1212;

	message = otUdpNewMessage(aInstance, NULL);
	if (message == NULL) {
		printf("Error creating udp message\n");
		return;
	}

	error = otMessageAppend(message, &temperature, 1);
	if (error != OT_ERROR_NONE && message != NULL) {
		printf("Error appending to udp message\n");
		otMessageFree(message);
		return;
	}

	error = otUdpSend(aInstance, &sUdpSocket, message, &messageInfo);
	if (error != OT_ERROR_NONE && message != NULL) {
		printf("Error sending udp packet\n");
		otMessageFree(message);
	}
}

#define TPM_MESSAGE_LEN 100
uint8_t tpm_message[TPM_MESSAGE_LEN];

void send_tpm_packet(otInstance* ot)
{
	otError error = OT_ERROR_NONE;
	otMessage*   message;
	otMessageInfo messageInfo;
	otIp6Address destinationAddr;

	memset(&messageInfo, 0, sizeof(messageInfo));
	memset(tpm_message, 0xE1, TPM_MESSAGE_LEN);

	otIp6AddressFromString("fe80::4873:c036:da29:d88b", &destinationAddr);
	/* otIp6AddressFromString("fde3:8f5e:f206:2::c0a8:0246", &destinationAddr); */
	messageInfo.mPeerAddr = destinationAddr;
	messageInfo.mPeerPort = 1212;

	message = otUdpNewMessage(ot, NULL);
	if (message == NULL) {
		/* printf("Error creating UDP message\n"); */
		return;
	}

	error = otMessageAppend(message, tpm_message, TPM_MESSAGE_LEN);
	if (error != OT_ERROR_NONE && message != NULL) {
		/* printf("Error appending to UDP message\n"); */
		otMessageFree(message);
		return;
	}

	error = otUdpSend(ot, &sUdpSocket, message, &messageInfo);
	if (error != OT_ERROR_NONE && message != NULL) {
		/* printf("Error sending udp packet: %d\n", error); */
		otMessageFree(message);
	}

	return;
}
