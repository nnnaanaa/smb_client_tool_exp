from smb.SMBConnection import SMBConnection
import os
import io
import sys

def download_smb_file_pysmb(server_ip, share_name, remote_path, local_save_path, username, password):
    """
    pysmb を使用してSMB共有からファイルをダウンロードします。
    """
    conn = None
    try:
        conn = SMBConnection(username, password, "client_machine", server_ip, use_ntlm_v2=True)
        print(f"[pysmb] SMBサーバー {server_ip} (ポート 445) への接続を試行中...", file=sys.stderr)
        conn.connect(server_ip, 445)
        print(f"[pysmb] SMBサーバー {server_ip} に接続しました。", file=sys.stderr)

        file_obj = io.BytesIO()
        print(f"[pysmb] 共有 '{share_name}' 上のリモートファイル '{remote_path}' をダウンロード中...", file=sys.stderr)
        file_attributes, filesize = conn.retrieveFile(share_name, remote_path, file_obj)
        file_obj.seek(0)
        with open(local_save_path, 'wb') as f:
            f.write(file_obj.read())

        print(f"\n[pysmb] ファイル '{remote_path}' ({filesize} バイト) を '{local_save_path}' にダウンロードしました。", file=sys.stderr)

    except Exception as e:
        print(f"\n[pysmb] エラーが発生しました: {e}", file=sys.stderr)
    finally:
        if conn:
            try:
                conn.close()
                print("[pysmb] SMB接続を閉じました。", file=sys.stderr)
            except Exception as e:
                print(f"[pysmb] 接続クリーンアップ中にエラー: {e}", file=sys.stderr)

SERVER_IP = "192.168.0.2"
SHARE_NAME = "admin"
REMOTE_FILE_PATH = "20231231\header-img.png"
LOCAL_SAVE_DIR = "."
LOCAL_SAVE_FILE_NAME = "header-img.png"
SMB_USERNAME = "admin"
SMB_PASSWORD = "Pa$$w0rd"

local_full_save_path = os.path.join(LOCAL_SAVE_DIR, LOCAL_SAVE_FILE_NAME)

if __name__ == "__main__":
    download_smb_file_pysmb(
        SERVER_IP,
        SHARE_NAME,
        REMOTE_FILE_PATH,
        local_full_save_path,
        SMB_USERNAME,
        SMB_PASSWORD
    )