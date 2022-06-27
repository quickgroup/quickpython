"""
    python-quick-captcha 1.0
"""
import logging, random, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter


class Captcha:

    # @staticmethod
    # def out(request):
    #     from django.shortcuts import HttpResponse
    #     event = request.GET.get("event", 'default')
    #     image_data, code = Captcha.generate()
    #     request.session['_captcha_' + event] = code
    #     return HttpResponse(image_data, content_type="image/png")

    @staticmethod
    def verify(request, text=None, event='default'):
        true_val = request.session.get('_captcha_' + event)
        if text is None or event is None or true_val is None:
            return False
        request.session['_captcha_' + event] = None       # 每次验证后都要求刷新验证码
        return str(text).lower() == str(true_val).lower()

    @staticmethod
    def generate():
        # 绘制干扰线
        def gene_line(draw, width, height, linecolor):
            # random.randint(a, b)用于生成一个指定范围内的证书，其中第一个参数a是上限，第二个参数b是下限，生成的随机数n：a<=n<=b
            begin = (random.randint(0, width), random.randint(0, height))
            end = (random.randint(0, width), random.randint(0, height))
            # 在图像上画线，参数值为线的起始和终止位置坐标[(x, y), (x, y)]和线的填充颜色
            draw.line([begin, end], fill=linecolor, width=2)

        # 生成验证码
        def gene_code(size, font_count, font_color, line_color):
            font_path = '{}/font.ttf'.format(os.path.dirname(os.path.abspath(__file__)))
            # 宽和高
            width, height = size
            # 创建图片, 'RGBA'表示4*8位像素，真彩+透明通道
            image = Image.new('RGB', (width, height), (255, 255, 255))
            # 验证码的字体。ImageFont这个函数从指定的文件加载了一个字体对象，并且为指定大小的字体创建了字体对象。
            font = ImageFont.truetype(font_path, 30)
            # 创建画笔，创建可用于绘制给定图像的对象
            draw = ImageDraw.Draw(image)
            # 随机生成想要的字符串
            font_count = random.randint(4, font_count)
            text = random.sample('ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789', font_count)
            text = ''.join(text)
            # 返回给定文本的宽度和高度，返回值为2元组
            font_width, font_height = font.getsize(text)
            # 填充字符串,参数分别是：文本的左上角坐标，文本内容，字体，文本的填充颜色
            draw.text(((width-font_width) / font_count, (height-font_height) / font_count), text, font=font, fill=font_color)
            # 画线的条数
            line_count = random.randint(2, 4)
            for i in range(line_count):
                gene_line(draw, width, height, line_color)
            # 滤镜，边界加强，ImageFilter.EDGE_ENHANCE_MORE为深度边缘增强滤波，会使得图像中边缘部分更加明显。
            image = image.filter(ImageFilter.EDGE_ENHANCE_MORE)
            # 保存验证码图片
            # image.save('idencode.png')

            from io import BytesIO
            with BytesIO() as f:
                image.save(f, format='JPEG')
                return f.getvalue(), text

        # TODO::调用生成
        size = (120, 50)        # 生成验证码图片的高度和宽度
        font_color = (0, 0, 255)     # 字体颜色，默认为蓝色
        line_color = (100, 100, 255)     # 线颜色，默认为蓝色
        return gene_code(size, 5, font_color, line_color)