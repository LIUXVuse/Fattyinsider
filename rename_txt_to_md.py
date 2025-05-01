import os
import argparse

def rename_files_in_directory(directory_path):
    """將指定目錄下的所有 .txt 文件重命名為 .md 文件。"""
    if not os.path.isdir(directory_path):
        print(f"錯誤：提供的路徑 '{directory_path}' 不是一個有效的目錄。")
        return

    print(f"開始處理目錄：{directory_path}")
    renamed_count = 0
    skipped_count = 0

    for filename in os.listdir(directory_path):
        if filename.endswith(".txt"):
            old_filepath = os.path.join(directory_path, filename)
            new_filename = filename[:-4] + ".md" # 將 .txt 替換為 .md
            new_filepath = os.path.join(directory_path, new_filename)

            try:
                os.rename(old_filepath, new_filepath)
                print(f"  已將 '{filename}' 重命名為 '{new_filename}'")
                renamed_count += 1
            except OSError as e:
                print(f"  重命名 '{filename}' 時發生錯誤: {e}")
                skipped_count += 1
        else:
            # print(f"  跳過非 .txt 文件: {filename}") # 可選：顯示跳過的文件
            pass

    print(f"\n處理完成。成功重命名 {renamed_count} 個文件，跳過或失敗 {skipped_count} 個文件。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="將指定目錄下的 .txt 文件重命名為 .md 文件。")
    parser.add_argument("directory", help="包含要重命名文件的目錄路徑。例如：S3EP201_204")

    args = parser.parse_args()

    rename_files_in_directory(args.directory) 