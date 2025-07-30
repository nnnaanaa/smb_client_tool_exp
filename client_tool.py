import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from smb.SMBConnection import SMBConnection
import os
import io
import sys
from datetime import datetime

class SMBClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SMB Client GUI App")
        self.root.geometry("1000x700") # ウィンドウの初期サイズを広げました

        self.conn = None
        self.current_smb_path = "/" 

        self.create_widgets()

    def create_widgets(self):
        # --- 設定フレーム ---
        settings_frame = ttk.LabelFrame(self.root, text="接続設定")
        settings_frame.pack(padx=10, pady=5, fill="x")

        ttk.Label(settings_frame, text="サーバーIP:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.server_ip_entry = ttk.Entry(settings_frame, width=30)
        self.server_ip_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.server_ip_entry.insert(0, "192.168.0.2")

        ttk.Label(settings_frame, text="共有名:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.share_name_entry = ttk.Entry(settings_frame, width=30)
        self.share_name_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        self.share_name_entry.insert(0, "admin")

        ttk.Label(settings_frame, text="ユーザー名:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.username_entry = ttk.Entry(settings_frame, width=30)
        self.username_entry.grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        self.username_entry.insert(0, "admin")

        ttk.Label(settings_frame, text="パスワード:").grid(row=3, column=0, padx=5, pady=2, sticky="w")
        self.password_entry = ttk.Entry(settings_frame, width=30, show="*")
        self.password_entry.grid(row=3, column=1, padx=5, pady=2, sticky="ew")
        self.password_entry.insert(0, "Pa$$w0rd")

        self.connect_button = ttk.Button(settings_frame, text="接続", command=self.connect_smb)
        self.connect_button.grid(row=0, column=2, rowspan=4, padx=10, pady=2, sticky="ns")

        settings_frame.columnconfigure(1, weight=1)

        # --- 現在のパス表示 ---
        path_frame = ttk.Frame(self.root)
        path_frame.pack(padx=10, pady=5, fill="x")
        ttk.Label(path_frame, text="現在のパス:").pack(side="left")
        self.current_path_label = ttk.Label(path_frame, text="/", foreground="blue")
        self.current_path_label.pack(side="left", padx=5)

        # --- ファイル/ディレクトリ表示ツリービュー ---
        # 修正箇所: 'columns' に "Last_Modified" を追加
        self.tree = ttk.Treeview(self.root, columns=("Name", "Type", "Size", "Last_Modified"), show="headings")
        
        # 修正箇所: 各列の見出しと幅を調整
        self.tree.heading("Name", text="ファイル名 / フォルダ名", anchor="w")
        self.tree.heading("Type", text="種類", anchor="center")
        self.tree.heading("Size", text="サイズ", anchor="e")
        self.tree.heading("Last_Modified", text="最終更新日", anchor="w") # 新しい列の見出し

        self.tree.column("Name", width=400, anchor="w", stretch=True) # ファイル名列を広げ、伸縮可能に
        self.tree.column("Type", width=70, anchor="center", stretch=False) # 種類列は固定幅
        self.tree.column("Size", width=120, anchor="e", stretch=False) # サイズ列は固定幅
        self.tree.column("Last_Modified", width=150, anchor="w", stretch=False) # 最終更新日列は固定幅
        
        self.tree.tag_configure('folder', background='#e0e0ff')
        self.tree.tag_configure('file', background='#f0f0f0')

        self.tree.pack(padx=10, pady=5, fill="both", expand=True)
        self.tree.bind("<Double-1>", self.on_item_double_click)

        # スクロールバー
        scrollbar = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # --- 操作ボタン ---
        button_frame = ttk.Frame(self.root)
        button_frame.pack(padx=10, pady=5, fill="x")

        self.parent_dir_button = ttk.Button(button_frame, text="上位ディレクトリへ", command=self.go_to_parent_directory)
        self.parent_dir_button.pack(side="left", padx=5)
        self.download_button = ttk.Button(button_frame, text="ファイルダウンロード", command=self.download_selected_file)
        self.download_button.pack(side="left", padx=5)

        # --- ステータスバー ---
        self.status_label = ttk.Label(self.root, text="準備完了", relief="sunken", anchor="w")
        self.status_label.pack(side="bottom", fill="x")

    def update_status(self, message, color="black"):
        self.status_label.config(text=message, foreground=color)
        self.root.update_idletasks()

    def connect_smb(self):
        server_ip = self.server_ip_entry.get()
        share_name = self.share_name_entry.get()
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not all([server_ip, share_name, username, password]):
            messagebox.showwarning("入力エラー", "すべての接続情報を入力してください。")
            return

        self.update_status("接続中...", "blue")
        try:
            if self.conn:
                try:
                    self.conn.close()
                except Exception:
                    pass

            self.conn = SMBConnection(username, password, "client_machine", server_ip, use_ntlm_v2=True)
            self.conn.connect(server_ip, 445)
            self.update_status(f"SMBサーバー {server_ip} に接続しました。", "green")
            self.browse_smb_path("/")
        except Exception as e:
            messagebox.showerror("接続エラー", f"SMBサーバーへの接続に失敗しました:\n{e}")
            self.update_status(f"接続失敗: {e}", "red")
            self.conn = None

    def browse_smb_path(self, path):
        if not self.conn:
            messagebox.showerror("エラー", "SMBサーバーに接続されていません。")
            return

        self.update_status(f"'{path}' の内容を取得中...", "blue")
        try:
            for i in self.tree.get_children():
                self.tree.delete(i)

            dir_list = self.conn.listPath(self.share_name_entry.get(), path)
            
            for item in dir_list:
                if item.filename in [".", ".."]:
                    continue

                # 最終更新日時をフォーマット
                last_modified_str = ""
                # item.last_write_time は Unix timestamp (秒) なので、datetime.fromtimestamp で変換
                if item.last_write_time is not None:
                    try:
                        dt_object = datetime.fromtimestamp(item.last_write_time)
                        last_modified_str = dt_object.strftime('%Y-%m-%d %H:%M')
                    except (ValueError, OSError): # 無効なタイムスタンプの場合
                        last_modified_str = "N/A" # Not Applicable

                if item.isDirectory:
                    # 修正箇所: values に last_modified_str を追加
                    self.tree.insert("", "end", text="", values=(item.filename, "フォルダ", "", last_modified_str), tags=('folder',))
                else:
                    # 修正箇所: values に last_modified_str を追加
                    self.tree.insert("", "end", text="", values=(item.filename, "ファイル", self.format_bytes(item.file_size), last_modified_str), tags=('file',))
            
            self.current_smb_path = path
            self.current_path_label.config(text=self.current_smb_path)
            self.update_status(f"'{path}' の内容を表示しました。", "green")

        except Exception as e:
            messagebox.showerror("パス参照エラー", f"パス '{path}' の内容取得に失敗しました:\n{e}")
            self.update_status(f"パス参照失敗: {e}", "red")

    def on_item_double_click(self, event):
        selected_item = self.tree.selection()
        if not selected_item:
            return

        item_id = selected_item[0]
        item_text = self.tree.item(item_id, "values")[0] # ファイル名/フォルダ名
        item_type = self.tree.item(item_id, "values")[1] # 種類

        if item_type == "フォルダ":
            new_path = os.path.join(self.current_smb_path, item_text).replace("\\", "/")
            self.browse_smb_path(new_path)

    def go_to_parent_directory(self):
        if self.current_smb_path == "/":
            return

        parent_path = os.path.dirname(self.current_smb_path).replace("\\", "/")
        if parent_path == "":
            parent_path = "/"
        self.browse_smb_path(parent_path)

    def download_selected_file(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("選択なし", "ダウンロードするファイルを選択してください。")
            return

        item_id = selected_item[0]
        item_text = self.tree.item(item_id, "values")[0] # ファイル名
        item_type = self.tree.item(item_id, "values")[1] # 種類

        if item_type == "フォルダ":
            messagebox.showwarning("フォルダのダウンロード", "フォルダは直接ダウンロードできません。")
            return

        remote_file_name = item_text
        remote_full_path = os.path.join(self.current_smb_path, remote_file_name).replace("\\", "/")
        
        local_save_path = filedialog.asksaveasfilename(
            initialdir=os.getcwd(),
            initialfile=remote_file_name,
            title="ファイルを保存"
        )

        if not local_save_path:
            self.update_status("ファイルの保存がキャンセルされました。", "orange")
            return

        self.update_status(f"'{remote_file_name}' をダウンロード中...", "blue")
        try:
            file_obj = io.BytesIO()
            file_attributes, filesize = self.conn.retrieveFile(self.share_name_entry.get(), remote_full_path, file_obj)
            
            file_obj.seek(0)
            with open(local_save_path, 'wb') as f:
                f.write(file_obj.read())

            self.update_status(f"'{remote_file_name}' を '{local_save_path}' にダウンロードしました ({self.format_bytes(filesize)})。", "green")
            messagebox.showinfo("ダウンロード完了", f"ファイル '{remote_file_name}' を正常にダウンロードしました。")
        except Exception as e:
            messagebox.showerror("ダウンロードエラー", f"ファイルのダウンロードに失敗しました:\n{e}")
            self.update_status(f"ダウンロード失敗: {e}", "red")

    def format_bytes(self, size):
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.2f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.2f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"

if __name__ == "__main__":
    root = tk.Tk()
    app = SMBClientApp(root)
    root.mainloop()