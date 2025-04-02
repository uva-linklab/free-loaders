# Makefile for user application

# Specify this directory relative to the current application.
ifndef TOCK_USERLAND_BASE_DIR
$(error TOCK_USERLAND_BASE_DIR must be set to path to libtock-c)
endif

# Which files to compile.
C_SRCS := $(wildcard *.c)

# Specify this app depends on the MTD OpenThread library.
include $(TOCK_USERLAND_BASE_DIR)/libopenthread/libopenthread-mtd.mk

# set stack size to 8000 to support openthread app
STACK_SIZE:=8000
APP_HEAP_SIZE:=5000

PACKAGE_NAME = org.tockos.thread-tutorial.openthread

TOCK_TARGETS = cortex-m4

# Include userland master makefile. Contains rules and flags for actually
# building the application.
include $(TOCK_USERLAND_BASE_DIR)/AppMakefile.mk
