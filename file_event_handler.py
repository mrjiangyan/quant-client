import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import importlib
import strategy
class MyEventHandler(FileSystemEventHandler):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def on_modified(self, event):
        if not event.is_directory:
            self.callback()

def reload_app():
    print("Reloading application...")  # 可以根据需要修改成重启应用的具体代码
    importlib.reload(strategy)
    # 这里可以添加重启应用的代码，例如重启服务器、重新加载模块等

def watch():
    path = "."  # 监视当前目录下的文件更改，你可以根据需要修改成特定的目录
    event_handler = MyEventHandler(reload_app)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        observer.join()
