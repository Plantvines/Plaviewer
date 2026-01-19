import webview
import os
import base64
import json
import re
import sys
import shutil
from PIL import Image

IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp'}

# 1. 実行ファイルの場所(BASE_DIR)を特定
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. カレントディレクトリを強制的にBASE_DIRに移動
os.chdir(BASE_DIR)

class Api:
    def __init__(self):
        self.base_dir = os.path.join(BASE_DIR, 'list')
        os.makedirs(self.base_dir, exist_ok=True)
        
    def get_lists(self):
        try:
            if not os.path.exists(self.base_dir):
                return []

            real_folders = [f for f in os.listdir(self.base_dir) if os.path.isdir(os.path.join(self.base_dir, f))]
            
            order_config_path = os.path.join(self.base_dir, 'lists.json')
            ordered_names = []
            if os.path.exists(order_config_path):
                try:
                    with open(order_config_path, 'r', encoding='utf-8') as f:
                        ordered_names = json.load(f)
                except:
                    pass

            folder_map = {}
            for name in real_folders:
                full_path = os.path.join(self.base_dir, name)
                folder_map[name] = {
                    "id": name,
                    "name": name,
                    "createdAt": os.path.getctime(full_path) * 1000
                }

            sorted_folders = []
            for name in ordered_names:
                if name in folder_map:
                    sorted_folders.append(folder_map[name])
                    del folder_map[name]
            
            for name in folder_map:
                sorted_folders.append(folder_map[name])

            return sorted_folders
        except Exception as e:
            print(f"List Error: {e}")
            return []

    def rename_list(self, old_name, new_name):
        old_path = os.path.join(self.base_dir, old_name)
        new_path = os.path.join(self.base_dir, new_name)
        try:
            if os.path.exists(new_path):
                return False
            os.rename(old_path, new_path)
            self._update_list_order_name(old_name, new_name)
            return True
        except Exception as e:
            print(f"Rename Error: {e}")
            return False

    def delete_list(self, folder_name):
        target_path = os.path.join(self.base_dir, folder_name)
        try:
            if os.path.exists(target_path):
                shutil.rmtree(target_path)
                self._remove_from_list_order(folder_name)
                return True
        except Exception as e:
            print(f"Delete List Error: {e}")
            return False

    def save_list_order(self, order_list):
        config_path = os.path.join(self.base_dir, 'lists.json')
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(order_list, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Save Order Error: {e}")
            return False

    def _update_list_order_name(self, old_name, new_name):
        config_path = os.path.join(self.base_dir, 'lists.json')
        if not os.path.exists(config_path): return
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if old_name in data:
                index = data.index(old_name)
                data[index] = new_name
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        except: pass

    def _remove_from_list_order(self, target_name):
        config_path = os.path.join(self.base_dir, 'lists.json')
        if not os.path.exists(config_path): return
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if target_name in data:
                data.remove(target_name)
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        except: pass

    def get_image_list(self, folder_name):
        print(f"★ リスト取得: {folder_name}")
        target_dir = os.path.join(self.base_dir, folder_name)
        metadata_path = os.path.join(target_dir, 'metadata.json')
        
        images = []
        metadata = {}

        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            except Exception as e:
                print(f"Metadata Load Error: {e}")

        if not os.path.exists(target_dir):
            return []

        try:
            files = os.listdir(target_dir)
            for filename in files:
                name, ext = os.path.splitext(filename)
                if ext.lower() in IMAGE_EXTS:
                    item_data = {
                        "id": filename,
                        "title": name,
                        "image": "", 
                        "date": os.path.getmtime(os.path.join(target_dir, filename)) * 1000,
                        "tags": [],
                        "favorite": False,
                        "love": False,
                        "bookmark": False,
                        "check": False,
                        "rating": "all",
                        "caption": ""
                    }
                    if filename in metadata:
                        saved_data = metadata[filename]
                        for key in saved_data:
                            if key not in ['id', 'image']:
                                item_data[key] = saved_data[key]
                    images.append(item_data)
            
            return images
        except Exception as e:
            print(f"Error: {e}")
            return []

    def create_new_list(self, folder_name):
        path = os.path.join(self.base_dir, folder_name)
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except:
            return False

    def save_metadata(self, folder_name, data_json):
        # オートセーブ用: 頻繁に呼ばれても大丈夫なようにサイレントにする
        target_dir = os.path.join(self.base_dir, folder_name)
        metadata_path = os.path.join(target_dir, 'metadata.json')

        save_dict = {}
        for item in data_json:
            clean_item = {k: v for k, v in item.items() if k not in ['image', 'tabId']}
            save_dict[item['id']] = clean_item

        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(save_dict, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Save Error: {e}")
            return False

    def delete_files(self, folder_name, filenames):
        print(f"★ 削除実行: {len(filenames)}件")
        target_dir = os.path.join(self.base_dir, folder_name)
        deleted_count = 0
        for fname in filenames:
            path = os.path.join(target_dir, fname)
            try:
                if os.path.exists(path):
                    os.remove(path)
                    deleted_count += 1
            except Exception as e:
                print(f"削除エラー ({fname}): {e}")
        return deleted_count

    def get_png_info(self, folder_name, filename):
        try:
            path = os.path.join(self.base_dir, folder_name, filename)
            if not os.path.exists(path):
                return "ファイルが見つかりません"
            with Image.open(path) as img:
                img.load()
                if 'parameters' in img.info:
                    return img.info['parameters']
                info_text = []
                for k, v in img.info.items():
                    if isinstance(v, str):
                        info_text.append(f"{k}: {v}")
                if not info_text:
                    return "PNG Infoなし"
                return "\n".join(info_text)
        except Exception as e:
            return f"読み込みエラー: {e}"

    def create_list_auto_rename(self, base_name):
        name = base_name
        counter = 1
        while os.path.exists(os.path.join(self.base_dir, name)):
            counter += 1
            name = f"{base_name} ({counter})"
        try:
            os.makedirs(os.path.join(self.base_dir, name))
            return name
        except Exception as e:
            print(f"Create List Error: {e}")
            return None

    def save_image_from_drop(self, folder_name, filename, b64_data):
        target_dir = os.path.join(self.base_dir, folder_name)
        if not os.path.exists(target_dir):
            return None
        base, ext = os.path.splitext(filename)
        name = filename
        counter = 1
        while os.path.exists(os.path.join(target_dir, name)):
            counter += 1
            name = f"{base} ({counter}){ext}"
        file_path = os.path.join(target_dir, name)
        try:
            if ',' in b64_data:
                header, encoded = b64_data.split(',', 1)
            else:
                encoded = b64_data
            data = base64.b64decode(encoded)
            with open(file_path, 'wb') as f:
                f.write(data)
            return name
        except Exception as e:
            print(f"Image Save Error: {e}")
            return None

    def open_folder(self, folder_name):
        try:
            path = os.path.join(self.base_dir, folder_name)
            if os.path.exists(path):
                os.startfile(path)
                return True
            else:
                return False
        except Exception as e:
            print(f"Open Folder Error: {e}")
            return False

    def move_image(self, source_folder, image_id, dest_folder):
        print(f"★ 移動: {image_id} -> {dest_folder}")
        if source_folder == dest_folder: return False

        src_path = os.path.join(self.base_dir, source_folder, image_id)
        dest_dir = os.path.join(self.base_dir, dest_folder)
        
        if not os.path.exists(src_path) or not os.path.exists(dest_dir):
            return False

        base, ext = os.path.splitext(image_id)
        new_filename = image_id
        counter = 1
        while os.path.exists(os.path.join(dest_dir, new_filename)):
            counter += 1
            new_filename = f"{base} ({counter}){ext}"
        
        dest_path = os.path.join(dest_dir, new_filename)
        
        try:
            shutil.move(src_path, dest_path)
            
            src_meta_path = os.path.join(self.base_dir, source_folder, 'metadata.json')
            moved_data = {}
            if os.path.exists(src_meta_path):
                try:
                    with open(src_meta_path, 'r', encoding='utf-8') as f:
                        src_data = json.load(f)
                    if image_id in src_data:
                        moved_data = src_data[image_id]
                        del src_data[image_id]
                        with open(src_meta_path, 'w', encoding='utf-8') as f:
                            json.dump(src_data, f, ensure_ascii=False, indent=2)
                except: pass

            dest_meta_path = os.path.join(dest_dir, 'metadata.json')
            dest_data = {}
            if os.path.exists(dest_meta_path):
                try:
                    with open(dest_meta_path, 'r', encoding='utf-8') as f:
                        dest_data = json.load(f)
                except: pass
            
            if moved_data:
                moved_data['id'] = new_filename
                dest_data[new_filename] = moved_data
            else:
                dest_data[new_filename] = {
                    "id": new_filename,
                    "title": os.path.splitext(new_filename)[0],
                    "date": os.path.getmtime(dest_path) * 1000
                }
                
            with open(dest_meta_path, 'w', encoding='utf-8') as f:
                json.dump(dest_data, f, ensure_ascii=False, indent=2)
                
            return True
        except Exception as e:
            print(f"Move Error: {e}")
            return False

api = Api()
html_path = os.path.join(BASE_DIR, 'index.html')

window = webview.create_window(
    title='Plaviewer v1.0 (AutoSave)', 
    url=html_path, 
    width=1200, 
    height=800, 
    js_api=api
)
webview.start(debug=False)