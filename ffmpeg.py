import os
import subprocess
import re
from ocr import do_ocr
class FfmpegHandle():
    def __init__(self, video_path, subtitle_area):
        self.video_path = video_path
        self.ymin = subtitle_area[0]
        self.ymax = subtitle_area[1]
        self.xmin = subtitle_area[2]
        self.xmax = subtitle_area[3]
        self.isFinished = False
    def run(self):
        x_left,y_top,sub_width,sub_height = self.xmin, self.ymin, self.xmax-self.xmin, self.ymax-self.ymin
        video_dir = os.path.dirname(self.video_path).replace("\\","/")
        video_name = self.video_path.split("/")[-1]
        images_path = os.path.join(video_dir,'images')
        if not os.path.exists(images_path):
            os.mkdir(images_path)
        else:
            import shutil
            shutil.rmtree(images_path, True)
            os.mkdir(images_path)
        ffmpeg_prefix = 'ffmpeg -hide_banner -loglevel error'
        clip_video_cmd = f'{ffmpeg_prefix} -i "{self.video_path}" -vf "crop=x={x_left}:y={y_top}:w={sub_width}:h={sub_height},fps=1" {images_path}/image-%05d.jpg'
        # subprocess.call(clip_video_cmd, shell=True)
        if os.path.exists(os.path.join(video_dir,video_name+".jpg")):
            print(f"该视频已被处理过，将被跳过，如需重新处理，请删除{video_name}.jpg文件")
            self.isFinished = True
        else:
            print("正在截取字幕帧，请耐心等待...")
            if subprocess.call(clip_video_cmd) == 0:
                print("字幕帧截取完成")
                # 开始进行拼接
                files = os.listdir(images_path)
                files = list(filter(lambda x : re.match(r'image-\d{5}\.jpg',x), files))
                image_count = len(files)
                concat_pic_cmd = f'{ffmpeg_prefix} -i {images_path}/image-%05d.jpg -filter_complex "tile=1x{image_count}" "{video_dir}/{video_name}.jpg"'
                if subprocess.call(concat_pic_cmd) == 0:
                    print("字幕帧拼接完成")
                    # 进行ocr识别
                    # files = list(filter(lambda x : re.match(r'.*\.jpg',x), os.listdir(os.path.dirname(video_dir))))
                    # print("正在进行OCR识别，请耐心等待...")
                    # if do_ocr(files, self.video_path):
                    #     print(f"视频文件 '{self.video_path}' OCR完成")
                    # else:
                    #     print(f"视频文件 '{self.video_path}' OCR出错!")
                    self.isFinished = True
            # print("retval",retval)