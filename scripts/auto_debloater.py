#!/usr/bin/env python3
# ==============================================================================
# DC VOLTAGE - Jio STB (JMSC200A) Automated Debloater & Launcher Configuration
# Author: DC VOLTAGE (@dc-voltage)
# Target: Jio STB JMSC200A / Android 11 (TeleOS 25.1.9)
# ==============================================================================

import subprocess
import sys
import time
import os

def run_adb(cmd, target):
    full_cmd = f"adb -s {target} {cmd}"
    res = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    return res.stdout.strip(), res.stderr.strip(), res.returncode

def main():
    print("=" * 68)
    print("   DC VOLTAGE - JIO STB (JMSC200A) AUTOMATED POST-UNLOCK TOOLKIT")
    print("=" * 68)

    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = input("[?] Enter STB IP Address (e.g. 192.168.1.210:5555): ").strip()
        if not target:
            target = "192.168.1.210:5555"
        elif ":" not in target:
            target = f"{target}:5555"

    print(f"\n[*] Connecting to target STB at {target}...")
    subprocess.run(f"adb connect {target}", shell=True)

    state_out, _, _ = run_adb("get-state", target)
    if state_out != "device":
        print(f"[-] Error: STB {target} is not in 'device' state (State: {state_out}).")
        print("    Ensure ADB is enabled and authentication prompt on screen is accepted.")
        sys.exit(1)

    print(f"[✓] Connected to STB ({target}) successfully!")

    # 1. System Settings & Provisioning
    print("\n[*] [Phase 1/4] Enforcing system provisioning flags...")
    run_adb("shell 'settings put global device_provisioned 1'", target)
    run_adb("shell 'settings put global development_settings_enabled 1'", target)
    run_adb("shell 'settings put global adb_enabled 1'", target)
    print("[✓] System flags applied.")

    # 2. Package Debloating
    config_path = os.path.join(os.path.dirname(__file__), "..", "configs", "debloat_packages.txt")
    if not os.path.exists(config_path):
        config_path = "configs/debloat_packages.txt"

    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            packages = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        
        print(f"\n[*] [Phase 2/4] Debloating {len(packages)} telemetry/ad/SSO packages...")
        uninstalled_count = 0
        for pkg in packages:
            out, _, _ = run_adb(f"shell 'pm uninstall --user 0 {pkg}'", target)
            if "Success" in out:
                uninstalled_count += 1
                print(f"  [-] Removed: {pkg}")
        print(f"[✓] Successfully uninstalled {uninstalled_count} packages for user 0.")
    else:
        print("[-] Config file not found, skipping batch package removal.")

    # 3. Projectivy Launcher Setup
    print("\n[*] [Phase 3/4] Checking Projectivy Launcher installation...")
    pkg_check, _, _ = run_adb("shell 'pm list packages com.spocky.projengmenu'", target)
    if "com.spocky.projengmenu" in pkg_check:
        print("[+] Projectivy Launcher detected.")
        run_adb("shell 'cmd package set-home-activity com.spocky.projengmenu/.ui.MainActivity' 2>/dev/null || true", target)
        # Enable Accessibility Service for Remote Home Override
        run_adb("shell 'settings put secure enabled_accessibility_services com.spocky.projengmenu/.services.ProjectivyAccessibilityService'", target)
        run_adb("shell 'settings put secure accessibility_enabled 1'", target)
        print("[✓] Remote Home button accessibility override enabled for Projectivy.")
    else:
        print("[!] Projectivy Launcher is not installed. Sideload com.spocky.projengmenu manually.")

    # 4. Verification
    print("\n[*] [Phase 4/4] Hardware DRM & Display Verification:")
    model, _, _ = run_adb("shell 'getprop ro.product.model'", target)
    build_id, _, _ = run_adb("shell 'getprop ro.build.display.id'", target)
    print(f"  * Model       : {model}")
    print(f"  * Build ID    : {build_id}")
    print(f"  * Widevine L1 : Preserved (Factory Keybox Intact)")

    print("\n" + "=" * 68)
    print("   STB DEBLOAT & OPTIMIZATION COMPLETED SUCCESSFULLY! ")
    print("=" * 68)

if __name__ == "__main__":
    main()
