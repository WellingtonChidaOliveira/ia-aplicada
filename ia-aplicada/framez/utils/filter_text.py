class FilterText:
    def __init__(self):
        self.blur_duration = 3.0
        self.fade_duration = 0.6
        self.text_fade = 0.8
        self.max_blur = 15

    def dark_filters(self):
        return (
            "scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,"
            "eq=brightness=-0.15:contrast=1.0:saturation=0.5:gamma=0.85,"
            "curves=r='0/0 0.5/0.38 1/0.85':g='0/0 0.5/0.40 1/0.88':b='0/0.04 0.5/0.48 1/0.95',"
            "colorbalance=rs=-0.25:gs=0.0:bs=0.15:rm=-0.1:gm=0.0:bm=0.05,"
            "eq=contrast=1.35:saturation=0.55:brightness=0.0,"
            "vignette=angle=PI/4:mode=forward"
        )

    def drawtext(self, text_file_path, alpha_expr):
        return (
            f"drawtext=textfile='{text_file_path}'"
            f":fontfile='/home/wchida/.local/share/fonts/BebasNeue-Regular.ttf'"
            f":fontsize=72"
            f":fontcolor=white@0.95"
            f":bordercolor=black:borderw=2"
            f":shadowcolor=black@0.8:shadowx=4:shadowy=4"
            f":line_spacing=12"
            f":text_align=center"
            f":x=(w-text_w)/2"
            f":y=h*0.78"
            f":alpha='{alpha_expr}'"
        )

    def filter_complex(self, text_file_path, duration):
        sharp_duration = duration - self.blur_duration

        filter_complex = (
            # TRECHO COM BLUR: primeiros blur_duration segundos
            f"[0:v]trim=start=0:end={self.blur_duration:.1f},setpts=PTS-STARTPTS,"
            f"{self.dark_filters()},"
            f"boxblur={self.max_blur}:{self.max_blur},"
            f"{self.drawtext(text_file_path, f'if(lt(t\\,{self.text_fade})\\,t/{self.text_fade}\\,1)')},"
            f"fade=t=out:st={self.blur_duration - self.fade_duration:.2f}:d={self.fade_duration}"
            f"[blurred];"
            # TRECHO NÍTIDO: resto do vídeo
            f"[0:v]trim=start={self.blur_duration:.1f},setpts=PTS-STARTPTS,"
            f"{self.dark_filters()},"
            f"{self.drawtext(text_file_path, f'if(gt(t\\,{sharp_duration - self.text_fade:.2f})\\,({sharp_duration:.2f}-t)/{self.text_fade}\\,1)')},"
            f"fade=t=in:st=0:d={self.fade_duration}"
            f"[sharp];"
            # CONCAT
            f"[blurred][sharp]concat=n=2:v=1:a=0[vout]"
        )
        return filter_complex
