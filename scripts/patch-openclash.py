import os
import sys

def patch_openclash(repo_dir):
    print(f"[*] Applying Chitanda patches to OpenClash: {repo_dir}")
    lua_file = os.path.join(repo_dir, "luci-app-openclash", "root", "usr", "share", "openclash", "openclash_version.lua")
    sh_file = os.path.join(repo_dir, "luci-app-openclash", "root", "usr", "share", "openclash", "openclash_core.sh")

    # 1. Patch openclash_version.lua
    if os.path.exists(lua_file):
        with open(lua_file, "r", encoding="utf-8") as f:
            lua_content = f.read()

        if "CHITANDA_MIHOMO_VERSION_URL" not in lua_content:
            target_str = 'local CDN_CACHE_FILE = "/tmp/openclash_cdn_info.json"'
            inject_str = target_str + '\nlocal CHITANDA_MIHOMO_VERSION_URL = "https://raw.githubusercontent.com/violetaini/chitanda/main/releases/mihomo/version.txt"'
            lua_content = lua_content.replace(target_str, inject_str, 1)

            func_def = """local function fetch_chitanda_mihomo_version()
	local raw = try_fetch({ CHITANDA_MIHOMO_VERSION_URL }, function(buf)
		local version = trim((buf or ""):match("^[^\n\r]*") or "")
		return version:match("^v?%d+%.%d+%.%d+[%w%._%-]*$") ~= nil
	end)
	local version = trim((raw or ""):match("^[^\n\r]*") or "")
	if version:match("^v?%d+%.%d+%.%d+[%w%._%-]*$") then
		return version
	end
	return ""
end
"""
            # inject before function M.prepare_oix_cdn_data
            target_func = "function M.prepare_oix_cdn_data(force)"
            lua_content = lua_content.replace(target_func, func_def + "\n" + target_func, 1)

            # inject core_meta_latest call
            target_meta = 'if not cur_oix then\n\t\t\tlocal core_raw'
            inject_meta = 'if not cur_oix then\n\t\t\tcore_meta_latest = fetch_chitanda_mihomo_version()\n\n\t\t\tlocal core_raw'
            if target_meta in lua_content:
                lua_content = lua_content.replace(target_meta, inject_meta, 1)
            else:
                target_meta2 = 'if not cur_oix then'
                inject_meta2 = 'if not cur_oix then\n\t\t\tcore_meta_latest = fetch_chitanda_mihomo_version()'
                lua_content = lua_content.replace(target_meta2, inject_meta2, 1)

            with open(lua_file, "w", encoding="utf-8") as f:
                f.write(lua_content)
            print("  [+] Patched openclash_version.lua")

    # 2. Patch openclash_core.sh
    if os.path.exists(sh_file):
        with open(sh_file, "r", encoding="utf-8") as f:
            sh_content = f.read()

        if "CHITANDA_CORE_RELEASE" not in sh_content:
            t1 = 'RELEASE_BRANCH=$(uci_get_config "release_branch" || echo "master")'
            i1 = t1 + '\nCHITANDA_CORE_RELEASE="https://github.com/violetaini/chitanda/releases/download"'
            sh_content = sh_content.replace(t1, i1, 1)

            t2 = 'TARGET_CORE_PATH="$meta_core_path"'
            i2 = t2 + '\nCHITANDA_CORE_VERSION_FILE="$meta_core_path/.chitanda-mihomo-version"\nCHITANDA_CORE_VERSION=$(cat "$CHITANDA_CORE_VERSION_FILE" 2>/dev/null)'
            sh_content = sh_content.replace(t2, i2, 1)

            t3 = 'if [ -n "$DIRECT_CORE_URL" ] || [ "$CORE_CV" != "$CORE_LV" ] || [ -z "$CORE_CV" ]; then'
            i3 = 'if [ -n "$DIRECT_CORE_URL" ] || [ "$CORE_TYPE" = "Meta" -a "$CHITANDA_CORE_VERSION" != "$CORE_LV" ] || [ "$CORE_CV" != "$CORE_LV" ] || [ -z "$CORE_CV" ]; then'
            sh_content = sh_content.replace(t3, i3, 1)

            t4 = 'if [ "$github_address_mod" != "0" ]; then'
            i4 = 'if [ "$CORE_TYPE" = "Meta" ]; then\n            DOWNLOAD_URL="${CHITANDA_CORE_RELEASE}/${CORE_LV}/clash-${CPU_MODEL}.tar.gz"\n         elif [ "$github_address_mod" != "0" ]; then'
            sh_content = sh_content.replace(t4, i4, 1)

            t5 = 'LOG_TIP "【"$CORE_TYPE"】Core Update Successful"'
            i5 = 'if [ "$CORE_TYPE" = "Meta" ]; then\n                     printf \'%s\\n\' "$CORE_LV" > "$CHITANDA_CORE_VERSION_FILE"\n                  fi\n                  LOG_TIP "【"$CORE_TYPE"】Core Update Successful"'
            sh_content = sh_content.replace(t5, i5, 1)

            with open(sh_file, "w", encoding="utf-8") as f:
                f.write(sh_content)
            print("  [+] Patched openclash_core.sh")

    print("[*] OpenClash Chitanda patching complete!")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    patch_openclash(target)
