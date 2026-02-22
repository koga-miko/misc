/* statig_json_cffi.h - Voice Recognition State Machine CFFI */
#ifndef STATIG_JSON_CFFI_H
#define STATIG_JSON_CFFI_H

#ifdef __cplusplus
extern "C" {
#endif

/* Opaque handle to the voice system */
typedef struct VoiceSystemHandle VoiceSystemHandle;

/**
 * Callback function type for state entry/exit notifications.
 *
 * kind: 0 = entry (about to enter a state), 1 = exit (about to leave a state)
 * json: NULL-terminated UTF-8 JSON string with details:
 *       {"sm":"<StateMachineName>","state":"<StateName>","kind":"entry"|"exit"}
 *       The string is only valid for the duration of the callback invocation.
 */
typedef void (*state_callback_t)(int kind, const char *json);

/**
 * Create a new voice recognition system.
 *
 * callback: Optional callback for state entry/exit notifications.
 *           Pass NULL to disable callbacks.
 * Returns NULL on failure.
 * The returned handle must be freed with destroy_voice_system().
 */
VoiceSystemHandle *create_voice_system(state_callback_t callback);

/**
 * Destroy a voice recognition system and free all resources.
 * handle may be NULL (no-op).
 */
void destroy_voice_system(VoiceSystemHandle *handle);

/**
 * Handle a JSON event and return the result as a JSON string.
 *
 * json_ptr: NULL-terminated UTF-8 JSON string.
 * Returns: NULL-terminated UTF-8 JSON response string.
 *          The returned pointer is valid until the next call to
 *          handle_event() or destroy_voice_system().
 *          Returns NULL on failure.
 */
const char *handle_event(VoiceSystemHandle *handle, const char *json_ptr);

/**
 * Get the current state as a JSON string.
 *
 * Returns: NULL-terminated UTF-8 JSON string.
 *          The returned pointer is valid until the next call to
 *          get_current_state() or destroy_voice_system().
 *          Returns NULL on failure.
 */
const char *get_current_state(VoiceSystemHandle *handle);

#ifdef __cplusplus
}
#endif

#endif /* STATIG_JSON_CFFI_H */
