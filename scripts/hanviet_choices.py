"""Han-Viet picks for characters whose sourced candidate list (Wiktionary / Unihan) mixes in Nom readings.

Every pick must be one of the sourced candidates (hanviet.py ignores a pick that is not), so this table
only *selects*; it never introduces a reading. CHOICE_TEXT = confident picks. LOWCONF_TEXT = best guess,
the word still gets hanviet_check so Quan sees it.
"""

CHOICE_TEXT = """
子:tử 不:bất 上:thượng 出:xuất 到:đáo 实:thực 动:động 成:thành 车:xa 中:trung 理:lí 作:tác 平:bình
期:kì 过:quá 前:tiền 话:thoại 色:sắc 主:chủ 场:trường 现:hiện 要:yếu 部:bộ 本:bản 见:kiến 快:khoái
观:quan 结:kết 整:chỉnh 去:khứ 个:cá 女:nữ 正:chính 道:đạo 单:đơn 度:độ 片:phiến 收:thu 运:vận
反:phản 起:khởi 听:thính 全:toàn 感:cảm 可:khả 格:cách 总:tổng 从:tòng 当:đương 件:kiện 受:thụ
取:thủ 确:xác 步:bộ 员:viên 台:đài 念:niệm 形:hình 比:tỉ 风:phong 复:phục 位:vị 提:đề 待:đãi
紧:khẩn 具:cụ 任:nhiệm 请:thỉnh 音:âm 级:cấp 广:quảng 组:tổ 演:diễn 造:tạo 术:thuật 消:tiêu 等:đẳng
晚:vãn 必:tất 讲:giảng 近:cận 持:trì 领:lĩnh 费:phí 内:nội 纪:kỉ 强:cường 指:chỉ 统:thống 班:ban
住:trú 们:môn 候:hậu 满:mãn 共:cộng 刻:khắc 练:luyện 标:tiêu 达:đạt 类:loại 料:liệu 病:bệnh 站:trạm
次:thứ 毛:mao 哪:na 写:tả 星:tinh 习:tập 衣:y 元:nguyên 思:tư 短:đoản 活:hoạt 养:dưỡng 愿:nguyện
播:bá 展:triển 式:thức 性:tính 各:các 景:cảnh 似:tự 此:thử 季:quý 鲜:tiên 读:độc 房:phòng 奶:nãi
朋:bằng 月:nguyệt 备:bị 铁:thiết 适:thích 画:hoạ 轻:khinh 原:nguyên 存:tồn 化:hoá 架:giá 牌:bài
尽:tận 张:trương 农:nông 烈:liệt 退:thoái 志:chí 含:hàm 获:hoạch 培:bồi 质:chất 投:đầu 唱:xướng
歌:ca 姐:thư 零:linh 走:tẩu 带:đới 份:phần 红:hồng 省:tỉnh 药:dược 因:nhân 创:sáng 区:khu 配:phối
根:căn 联:liên 属:thuộc 简:giản 苦:khổ 义:nghĩa 抓:trảo 括:quát 免:miễn 潮:triều 促:xúc 袋:đại
源:nguyên 挥:huy 轮:luân 限:hạn 刷:xoát 引:dẫn 项:hạng 治:trị 错:thố 弟:đệ 兴:hưng 哥:ca 孩:hài
答:đáp 洗:tẩy 怎:chẩm 知:tri 超:siêu 故:cố 板:bản 或:hoặc 普:phổ 顺:thuận 万:vạn 许:hứa 座:toạ
被:bị 吵:sảo 约:ước 订:đính 福:phúc 察:sát 庆:khánh 议:nghị 基:cơ 容:dung 升:thăng 石:thạch 首:thủ
谈:đàm 跳:khiêu 箱:tương 追:truy 摆:bãi 沉:trầm 序:tự 纯:thuần 刺:thích 销:tiêu 淡:đạm 松:tùng
趣:thú 渐:tiệm 泪:lệ 稳:ổn 牙:nha 严:nghiêm 给:cấp 贵:quý 两:lưỡng 慢:mạn 拿:nã 牛:ngưu 喜:hỉ
欢:hoan 远:viễn 左:tả 分:phân 查:tra 段:đoạn 迎:nghênh 检:kiểm 舒:thư 态:thái 已:dĩ 言:ngôn 按:án
补:bổ 曾:tằng 城:thành 厂:xưởng 村:thôn 娘:nương 注:chú 互:hỗ 将:tương 拍:phách 评:bình 政:chính 规:quy 李:lý 齐:tề
散:tản 舞:vũ 突:đột 危:nguy 武:vũ 败:bại 守:thủ 迫:bách 与:dữ 抄:sao 诚:thành 迟:trì 粗:thô 摇:dao
豆:đậu 肥:phì 斗:đấu 减:giảm 竟:cánh 镜:kính 宽:khoan 扩:khuếch 巾:cân 描:miêu 权:quyền 燃:nhiên
王:vương 著:trứ 依:y 圆:viên 穿:xuyên 诉:tố 汉:hán 块:khối 累:lụy 六:lục 吗:ma 也:dã 草:thảo 吹:xuy
应:ứng 且:thả 斤:cân 司:ti 顾:cố 庭:đình 句:câu 堂:đường 爬:ba 晴:tình 秋:thu 般:ban 占:chiếm
搬:ban 杂:tạp 冒:mạo 困:khốn 媒:môi 胖:bàn 币:tệ 伟:vĩ 血:huyết 压:áp 戏:hí 增:tăng 猪:trư 彻:triệt
措:thố 扫:tảo 顶:đỉnh 耳:nhĩ 映:ánh 妻:thê 符:phù 盖:cái 供:cung 距:cự 聚:tụ 递:đệ 厘:li 摸:mạc
浅:thiển 趋:xu 圈:khuyên 弱:nhược 孙:tôn 殊:thù 络:lạc 胸:hung 幼:ấu 招:chiêu 召:triệu 池:trì 滑:hoạt
敏:mẫn 姥:mỗ 令:lệnh 绕:nhiễu 软:nhuyễn 丝:ty 仿:phảng 润:nhuận 私:tư 跟:cân 绍:thiệu 渴:khát 呢:ni
旁:bàng 掉:điệu 康:khang 篮:lam 鸟:điểu 弄:lộng 宜:nghi 漂:phiêu 楚:sở 让:nhượng 发:phát 腿:thoái
惯:quán 己:kỷ 衫:sam 丽:lệ 汤:thang 希:hy 姨:di 扬:dương 擦:sát 炼:luyện 江:giang 授:thụ 禁:cấm
虑:lự 棵:khỏa 矿:khoáng 伞:tản 甚:thậm 躺:thảng 慰:uý 炮:pháo 凌:lăng 拆:sách 宠:sủng 厦:hạ 耽:đam
滴:trích 毯:thảm 朵:đóa 罚:phạt 繁:phồn 碍:ngại 冠:quan 滚:cổn 慌:hoảng 宾:tân 烂:lạn 域:vực 漏:lậu
苗:miêu 仔:tử 披:phi 枪:thương 劝:khuyến 忍:nhẫn 摄:nhiếp 损:tổn 锁:toả 拳:quyền 淘:đào 委:uỷ 屈:khuất
勿:vật 吓:hách 押:áp 咬:giảo 素:tố 珍:trân 织:chức 彼:bỉ 毒:độc 惭:tàm 炒:sao 厢:sương 臭:xú 版:bản
喷:phún 洞:động 佛:phật 疯:phong 幅:bức 钢:cương 股:cổ 泛:phiếm 纳:nạp 蝴:hồ 幻:huyễn 尘:trần 寂:tịch
夹:giáp 剪:tiễn 胶:giao 狡:giảo 俱:câu 拦:lan 梨:lê 逻:la 矛:mâu 煤:môi 炭:thán 偶:ngẫu 匹:thất
凭:bằng 杀:sát 漠:mạc 射:xạ 搜:sưu 宿:túc 纲:cương 吐:thổ 歪:oai 唯:duy 吻:vẫn 奈:nại 雾:vụ 艳:diễm
憾:hám 涨:trướng 哲:triết
"""

LOWCONF_TEXT = """
吃:ngật 找:trảo 划:hoa 妈:ma 哈:ha 劲:kình 汁:trấp 呀:nha 歇:yết 挣:tránh 拼:phanh
"""


def parse(text):
    return dict(item.split(":") for item in text.split())


CHOICE = parse(CHOICE_TEXT)
LOWCONF = parse(LOWCONF_TEXT)
