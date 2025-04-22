#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>


#include <libtock-sync/services/alarm.h>
#include <libtock/interface/button.h>
#include <libtock/kernel/ipc.h>
#include <libtock/services/alarm.h>
#include <libtock/tock.h>

#include <libopenthread/platform/openthread-system.h>
#include <libopenthread/platform/plat.h>
#include <openthread/dataset_ftd.h>
#include <openthread/instance.h>
#include <openthread/ip6.h>
#include <openthread/platform/alarm-milli.h>
#include <openthread/tasklet.h>
#include <openthread/thread.h>
#include <openthread/udp.h>

#include "acls.h"
#include "acls-config.h"

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

#define FL_CONTROLLER_IP6_STR "2001:470:5:9af:1::fe01"
#define FL_CONTROLLER_IP4_IP6_STR "fde3:8f5e:f206:2::c0a8:023d"
#define BORDER_ROUTER_IP6_STR "fe80::4873:c036:da29:d88b"

bool _g_ready = false;
uint32_t _g_last_pressed_debounce_ms = 0;
bool _g_send_offload = false;
void button_cb_offload_audio(
	__attribute__ ((unused)) returncode_t rtc,
	__attribute__ ((unused)) int button_no,
	bool pressed);

void run_sample_classification(__attribute__ ((unused)) returncode_t rtc,
							   __attribute__ ((unused)) int button_no,
							   bool pressed);

// helper utility to print ip address
static void print_ip_addr(otInstance* instance);

otInstance* _g_instance = NULL;

// OPTIONS:
// 1. Use prepared audio. ==============
#include "sample-data.h"
const uint16_t* const _g_audio_samples = MDL_SampleAudio;
// 2. Capture audio with the ADC. ======
/* uint16_t _g_audio_samples[ACLS_SAMPLE_LEN]; */
// =====================================

#define MAX_UDP_PAYLOAD_BYTES 79

int main(__attribute__((unused)) int argc, __attribute__((unused)) char* argv[]) {
	// Write to the audio sample buffer to make sure the entire buffer is writeable.
	/* for (uint32_t i = 0; i < ACLS_SAMPLE_LEN; i++) */
	/* { */
	/* 	_g_audio_samples[i] = 0xACFE; */
	/* } */

	// Let ACLS check its buffers.
	check_initialize();

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

	otError error = OT_ERROR_NONE;
	otMessageInfo messageInfo;
	otIp6Address destinationAddr;

	memset(&messageInfo, 0, sizeof(messageInfo));

	error = otIp6AddressFromString(BORDER_ROUTER_IP6_STR, &destinationAddr);
	if (error != OT_ERROR_NONE) {
		printf("Failed to convert destination address.\n");
		while (true) {  }
	}
	messageInfo.mPeerAddr = destinationAddr;
	messageInfo.mPeerPort = 12122;

	uint32_t t_offload_start;
	uint32_t t_offload_done;


	// Set up button callback.
	libtock_button_notify_on_press(0, button_cb_offload_audio);
	libtock_button_notify_on_press(1, run_sample_classification);

	//
	////////////////////////////////////////////////////

	// OpenThread main loop.
	uint32_t next_byte_idx = 0;
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

			// Offload to fReeLoaders when button is pressed.
			if (_g_send_offload && _g_ready) {
				const uint32_t offload_size_bytes = MDL_WAVTOC_SAMPLE_AUDIO_LEN * sizeof(uint16_t);
				if (next_byte_idx >= offload_size_bytes) {
					_g_send_offload = false;

					libtock_alarm_command_read(&t_offload_done);
					const uint32_t d_classify_ms = libtock_alarm_ticks_to_ms(t_offload_done - t_offload_start);
					printf("Offload done in %lu ms.\n", d_classify_ms);
					next_byte_idx = 0;
				} else {
					if (next_byte_idx == 0) {
						libtock_alarm_command_read(&t_offload_start);
					}

					otMessage* message = NULL;
					message = otUdpNewMessage(instance, NULL);
					if (message == NULL) {
						printf("Error creating UDP message.\n");
						continue;
					}

					const uint32_t bytes_pending = offload_size_bytes - next_byte_idx;
					const uint32_t message_len = bytes_pending < MAX_UDP_PAYLOAD_BYTES ? bytes_pending : MAX_UDP_PAYLOAD_BYTES;
					/* printf("Bytes pending: %lu\n", bytes_pending); */
					error = otMessageAppend(message, ((uint8_t*) _g_audio_samples) + next_byte_idx, message_len);
					if (error != OT_ERROR_NONE) {
						printf("Error appending to message.\n");
						otMessageFree(message);
						continue;
					}

					/* printf("sending... "); */
					error = otUdpSend(instance, &sUdpSocket, message, &messageInfo);
					if (error != OT_ERROR_NONE && message != NULL) {
						printf("error sending packet: %d\n", error);
						otMessageFree(message);
						continue;
					} else {
						next_byte_idx += message_len;
						/* printf("Sent %lu bytes.\n", message_len); */
					}
				}
			} else {
				yield();
			}
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
		_g_ready = false;
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

void button_cb_offload_audio(
	__attribute__ ((unused)) returncode_t rtc,
	__attribute__ ((unused)) int button_no,
	bool pressed)
{
	if (!_g_ready || !pressed) { return; }

	uint32_t t_now;
	uint32_t t_now_ms;
	libtock_alarm_command_read(&t_now);
	t_now_ms = libtock_alarm_ticks_to_ms(t_now);

	uint32_t d_last_pressed_ms = t_now_ms -_g_last_pressed_debounce_ms;
	if (d_last_pressed_ms < 300) { return; }
	_g_last_pressed_debounce_ms = t_now_ms;

	_g_send_offload = true;

	return;
}

void run_sample_classification(__attribute__ ((unused)) returncode_t rtc,
							   __attribute__ ((unused)) int button_no,
							   bool pressed)
{
	printf("Button event.\n");

	if (!pressed) { return; }

	uint32_t t_now;
	uint32_t t_now_ms;
	libtock_alarm_command_read(&t_now);
	t_now_ms = libtock_alarm_ticks_to_ms(t_now);

	uint32_t d_last_pressed_ms = t_now_ms -_g_last_pressed_debounce_ms;
	if (d_last_pressed_ms < 300) { return; }
	_g_last_pressed_debounce_ms = t_now_ms;

	otInstance* const ot = _g_instance;

	printf("Running classification...\n");
	classify(_g_audio_samples);
	uint32_t t_classify_done;
	libtock_alarm_command_read(&t_classify_done);
	const uint32_t d_classify_ms = libtock_alarm_ticks_to_ms(t_classify_done - t_now);
	printf("Done in %lu ms.\n", d_classify_ms);

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
