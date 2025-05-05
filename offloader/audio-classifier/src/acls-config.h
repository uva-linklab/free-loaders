#ifndef MDL_ACLSCONFIG_H
#define MDL_ACLSCONFIG_H

#define ACLS_SAMPLE_FREQ ((uint32_t) 11025)
// Make sure sample length is a power of 2.
// This affects buffer sizes for much of the audio classification code.
// Longer sampling durations means better results but consumes more RAM.
#define ACLS_SAMPLE_LEN ((uint32_t) 4096)
#define ACLS_SAMPLING_DURATION_MS ((uint32_t) (ACLS_SAMPLE_LEN * 1000) / ACLS_SAMPLE_FREQ)

#endif
