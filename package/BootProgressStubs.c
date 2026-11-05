// SPDX-License-Identifier: BSD-2-Clause-Patent
// r11 board stubs: weak stand-ins for the diagnostics the boot progress kit reads but
// this port does not link (USB console, eMMC probe, UFS, touch, Adreno, cpufreq,
// owner-root, virtio, boot-process/ui-trace counters, sched masks, armcpu deadline
// diagnostics). Data reads as zero and functions return zero; a real definition linked
// later takes precedence. Sources of the list: the kit weak_import externs missing from
// this kernel plus the actual linker undefined-symbol list (like sirius
// BootProgressStubs.c, generated there by scripts/gen-boot-progress-stubs.py).
#include <stdint.h>
#include <stddef.h>

__attribute__((weak)) volatile char armcpu_deadline_seen[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char armcpu_deadline_start[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char armcpu_deadline_ticks[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char armcpu_imem[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char armcpu_probe_accepted[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char armcpu_probe_boot_number[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char armcpu_probe_calls[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char armcpu_probe_declined_number[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char armcpu_probe_declined_type[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char armcpu_probe_last_number[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char armcpu_probe_last_reg[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char armcpu_probe_last_reg_len[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char armcpu_probe_last_type_len[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char armcpu_probe_smp_arg[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char armcpu_scm[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char armcpu_wdog[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char armcpu_wdog_live[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char armcpu_wdog_pets[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char boot_process_attempts[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char boot_process_busy[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char boot_process_passes[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char boot_process_rows[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char boot_process_seen[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char boot_progress_exit_fault[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char boot_progress_exit_reason[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char boot_progress_throw_text[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char boot_ui_trace_index[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char boot_ui_trace_label[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char boot_ui_trace_phase[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char boot_ui_trace_ready[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char boot_ui_trace_rows[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_adreno_audit_attr[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_adreno_audit_ticks[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_adreno_cache_stats[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_adreno_coherence[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_adreno_reassert_ticks[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_adreno_wc_audit[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_adreno_wc_distrusted[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_cpufreq_row[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_cpufreq_stage[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_data_persist_errors[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_data_persist_first_lba[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_data_persist_gpt[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_data_persist_gpt_after[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_data_persist_header[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_data_persist_loaded[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_data_persist_pages[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_data_persist_present[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_data_persist_state[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_data_persist_syncs[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_data_persist_writes[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_data_writeback_flushes[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_gop_gpu_abandoned[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_gop_gpu_completions[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_gop_gpu_failures[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_gop_gpu_offers[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_gop_virtual[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_hid_input_events[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_hid_input_results[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_client_calls[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_client_class[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_client_pid[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_client_status[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_client_type[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_copy_bytes_last[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_copy_bytes_sum[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_copy_last[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_copy_max[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_copy_n[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_copy_sum[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_frame_color_counts[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_frame_color_other[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_frame_colors[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_frame_count[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_frame_kind[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_frame_stats[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_frame_time[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_gop_bytes[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_gop_physical[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_gop_virtual[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_gpu_fallbacks[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_gpu_last_status[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_guard_slot[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_pm_callbacks[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_pm_calls[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_pm_stage[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_prepare_attempts[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_prepare_calls[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_prepare_reason[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_rej_class[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_rej_options[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_rej_reason[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_rej_size[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_rej_state[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_rej_surface[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_rej_surfaces[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_retirement_calls[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_stage[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_swap_accepted_count[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_swap_rejected_count[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_swap_validation_calls[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_swap_validation_reason[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_swap_validation_result[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_transfer_bytes[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_transfer_calls[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_legacy_transfer_status[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_owner_root_accepted[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_ram_block_bytes[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_ram_block_resident_bytes[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_ram_block_sparse[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_touch_count[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_touch_ids[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_touch_loop_step[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_touch_rows[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_touch_seq[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_touch_stage_req[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_touch_xs[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_touch_ys[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_ufs_block_failures[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_ufs_block_reads[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_ufs_blocks_published[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_ufs_integrity_failures[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_ufs_matched[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_ufs_probe_calls[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_ufs_read_ticks[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_ufs_root_failure[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_ufs_root_step[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_ufs_verified_blocks[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_ufs_verify_ticks[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_virtio_read_failures[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_virtio_read_requests[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_virtio_ready[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char native_virtio_verified_blocks[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char sched_pcpu_mask[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char sched_rcpu_mask[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char sirius_emmc_caps[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char sirius_emmc_clock[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char sirius_emmc_halts[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char sirius_emmc_power[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char sirius_emmc_state[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char sirius_emmc_step[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char sirius_emmc_version[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char sirius_usb_clk[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char sirius_usb_dsts[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char sirius_usb_dwc[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char sirius_usb_gcc[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char sirius_usb_pll[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char sirius_usb_smmu[4096] __attribute__((aligned(16)));
__attribute__((weak)) volatile char sirius_usb_step[4096] __attribute__((aligned(16)));

__attribute__((weak)) long armcpu_map_physical(void) { return 0; }
__attribute__((weak)) long armcpu_wdog_sample(void) { return 0; }
__attribute__((weak)) long boot_log_tick(void) { return 0; }
__attribute__((weak)) long boot_process_capture(void) { return 0; }
__attribute__((weak)) long boot_process_snapshot(void) { return 0; }
__attribute__((weak)) long boot_ui_trace_role_rows(void) { return 0; }
__attribute__((weak)) long boot_ui_trace_snapshot(void) { return 0; }
__attribute__((weak)) long native_touch_probe(void) { return 0; }
__attribute__((weak)) long native_ufs_progress_text(void) { return 0; }
__attribute__((weak)) long sheng_cpufreq_poll(void) { return 0; }
__attribute__((weak)) long sirius_usb_log_char(void) { return 0; }
__attribute__((weak)) long sirius_usb_poll(void) { return 0; }
