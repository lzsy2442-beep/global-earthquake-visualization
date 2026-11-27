# -*- coding: utf-8 -*-
"""把 USGS 的 place 字段归并成「国家 / 地区」级别，并提供中英文对照。

用于 M3 数据集：605,435 条记录如果存完整地名要 60 MB 以上，
改成 2 字节的地区编号，只增加约 1.2 MB。
"""
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from place_translate import COUNTRY_CN  # noqa: E402

# 方位词 / 修饰词前缀，归并时去掉
_PREFIX = re.compile(
    r"^(north|south|east|west|northeast|northwest|southeast|southwest) of (the )?"
    r"|^(central|southern|northern|eastern|western|off the (east|west|north|south) coast of|"
    r"off the coast of|near the|near|in the|in|the)\s+",
    re.I,
)
_SUFFIX = re.compile(r"\s+region$", re.I)

# 归并后的别名：台湾省不是地区级条目，统一并入中国
_ALIAS = {
    "Taiwan": "China",
    "Taiwan region": "China",
}


def region_of(place):
    """'83 km ESE of Hengchun, Taiwan' -> 'China'；'Japan region' -> 'Japan'。"""
    s = (place or "").strip()
    if not s:
        return ""
    prev = None
    while prev != s:
        prev = s
        s = _PREFIX.sub("", s).strip()
    if ", " in s:
        s = s.split(", ")[-1].strip()
        s = _PREFIX.sub("", s).strip()
    s = _SUFFIX.sub("", s).strip()
    s = _ALIAS.get(s, s)
    # 兜底：任何仍带 Taiwan 字样的地区（如 Taiwan Strait）也归入中国
    if s != "China" and "taiwan" in s.lower():
        return "China"
    return s


# 补充译名：COUNTRY_CN 没覆盖到的常见海域、洋中脊、岛屿
_EXTRA = {
    "South Sandwich Islands": "南桑威奇群岛",
    "Kermadec Islands": "克马德克群岛",
    "Mid-Atlantic Ridge": "中大西洋海岭",
    "East Pacific Rise": "东太平洋海隆",
    "Fiji Islands": "斐济群岛",
    "Pacific-Antarctic Ridge": "太平洋-南极海岭",
    "Loyalty Islands": "洛亚蒂群岛",
    "Mid-Indian Ridge": "中印度洋海岭",
    "Kuril Islands": "千岛群岛",
    "Macquarie Island": "麦夸里岛",
    "Balleny Islands": "巴利尼群岛",
    "West Chile Rise": "智利海岭西部",
    "Ascension Island": "阿森松岛",
    "Reykjanes Ridge": "雷克雅内斯海岭",
    "Mariana Islands": "马里亚纳群岛",
    "Easter Island": "复活节岛",
    "Carlsberg Ridge": "卡尔士伯格海岭",
    "Southwest Indian Ridge": "西南印度洋海岭",
    "Indian-Antarctic Ridge": "印度-南极海岭",
    "Banda Sea": "班达海",
    "Scotia Sea": "斯科舍海",
    "Africa": "非洲",
    "Prince Edward Islands": "爱德华王子群岛",
    "South Indian Ocean": "南印度洋",
    "Bouvet Island": "布韦岛",
    "Owen Fracture Zone": "欧文断裂带",
    "Chagos Archipelago": "查戈斯群岛",
    "Severnaya Zemlya": "北地群岛",
    "South Shetland Islands": "南设得兰群岛",
    "Mauritius - Reunion": "毛里求斯-留尼汪",
    "Xizang": "西藏",
    "South Georgia Island": "南乔治亚岛",
    "Indian Ocean Triple Junction": "印度洋三联点",
    "Drake Passage": "德雷克海峡",
    "North Island of New Zealand": "新西兰北岛",
    "Svalbard": "斯瓦尔巴群岛",
    "Tristan da Cunha": "特里斯坦-达库尼亚",
    "Revilla Gigedo Islands": "雷维亚希赫多群岛",
    "Greenland Sea": "格陵兰海",
    "North Indian Ocean": "北印度洋",
    "South Atlantic Ocean": "南大西洋",
    "Federated States of Micronesia": "密克罗尼西亚联邦",
    "Azores Islands": "亚速尔群岛",
    "Central America": "中美洲",
    "Molucca Sea": "马鲁古海",
    "South Pacific Ocean": "南太平洋",
    "North Pacific Ocean": "北太平洋",
    "Indian Ocean": "印度洋",
    "Atlantic Ocean": "大西洋",
    "Pacific Ocean": "太平洋",
    "Arctic Ocean": "北冰洋",
    "Southern Ocean": "南大洋",
    "Antarctica": "南极洲",
    "Antarctic Peninsula": "南极半岛",
    "Caribbean Sea": "加勒比海",
    "Gulf of California": "加利福尼亚湾",
    "Gulf of Alaska": "阿拉斯加湾",
    "Sea of Japan": "日本海",
    "Sea of Okhotsk": "鄂霍次克海",
    "Philippine Sea": "菲律宾海",
    "Celebes Sea": "西里伯斯海",
    "Java Sea": "爪哇海",
    "Flores Sea": "弗洛勒斯海",
    "Timor Sea": "帝汶海",
    "Arafura Sea": "阿拉弗拉海",
    "Coral Sea": "珊瑚海",
    "Tasman Sea": "塔斯曼海",
    "Andaman Sea": "安达曼海",
    "Arabian Sea": "阿拉伯海",
    "Bay of Bengal": "孟加拉湾",
    "Red Sea": "红海",
    "Mediterranean Sea": "地中海",
    "Aegean Sea": "爱琴海",
    "Black Sea": "黑海",
    "Caspian Sea": "里海",
    "Gulf of Aden": "亚丁湾",
    "Persian Gulf": "波斯湾",
    "Gulf of Mexico": "墨西哥湾",
    "Lake Baikal": "贝加尔湖",
    "Hindu Kush": "兴都库什",
    "Hokkaido": "北海道",
    "Honshu": "本州",
    "Kyushu": "九州",
    "Shikoku": "四国",
    "Ryukyu Islands": "琉球群岛",
    "Izu Islands": "伊豆群岛",
    "Bonin Islands": "小笠原群岛",
    "Volcano Islands": "火山列岛",
    "Taiwan region": "台湾地区",
    "Luzon": "吕宋岛",
    "Mindanao": "棉兰老岛",
    "Visayan Islands": "米沙鄢群岛",
    "Sulawesi": "苏拉威西",
    "Sumatra": "苏门答腊",
    "Java": "爪哇",
    "Bali": "巴厘",
    "Flores": "弗洛勒斯",
    "Sumba": "松巴",
    "Timor": "帝汶",
    "Halmahera": "哈马黑拉",
    "Seram": "塞兰",
    "New Britain": "新不列颠",
    "New Ireland": "新爱尔兰",
    "New Guinea": "新几内亚",
    "Bougainville": "布干维尔",
    "Guadalcanal": "瓜达尔卡纳尔",
    "Santa Cruz Islands": "圣克鲁斯群岛",
    "Vanuatu Islands": "瓦努阿图群岛",
    "Loyalty Islands": "洛亚蒂群岛",
    "New Caledonia": "新喀里多尼亚",
    "Tonga Islands": "汤加群岛",
    "Samoa Islands": "萨摩亚群岛",
    "Cook Islands": "库克群岛",
    "Society Islands": "社会群岛",
    "Tuamotu Archipelago": "土阿莫土群岛",
    "Marquesas Islands": "马克萨斯群岛",
    "Hawaii": "夏威夷",
    "Alaska Peninsula": "阿拉斯加半岛",
    "Aleutian Islands": "阿留申群岛",
    "Bering Sea": "白令海",
    "Queen Charlotte Islands": "夏洛特皇后群岛",
    "Vancouver Island": "温哥华岛",
    "California": "加利福尼亚",
    "Nevada": "内华达",
    "Utah": "犹他",
    "Montana": "蒙大拿",
    "Idaho": "爱达荷",
    "Wyoming": "怀俄明",
    "Washington": "华盛顿州",
    "Oregon": "俄勒冈",
    "Puerto Rico": "波多黎各",
    "Virgin Islands": "维尔京群岛",
    "Lesser Antilles": "小安的列斯群岛",
    "Cuba": "古巴",
    "Jamaica": "牙买加",
    "Haiti": "海地",
    "Dominican Republic": "多米尼加",
    "Costa Rica": "哥斯达黎加",
    "El Salvador": "萨尔瓦多",
    "Guatemala": "危地马拉",
    "Honduras": "洪都拉斯",
    "Nicaragua": "尼加拉瓜",
    "Panama": "巴拿马",
    "North Atlantic Ocean": "北大西洋",
    "Norwegian Sea": "挪威海",
    "Galapagos Islands": "加拉帕戈斯群岛",
    "Galapagos Triple Junction": "加拉帕戈斯三联点",
    "Philippine Islands": "菲律宾群岛",
    "Southeast Indian Ridge": "东南印度洋海岭",
    "D'Entrecasteaux Islands": "当特尔卡斯托群岛",
    "America": "美洲",
    "South Island of New Zealand": "新西兰南岛",
}


def region_cn(region):
    if not region:
        return ""
    return _EXTRA.get(region) or COUNTRY_CN.get(region) or region


if __name__ == "__main__":
    # 自检：打印几条归并结果
    for p in ["83 km ESE of Hengchun, Taiwan", "Japan region",
              "south of the Fiji Islands", "South Sandwich Islands region",
              "off the west coast of northern Sumatra"]:
        r = region_of(p)
        print("%-45s -> %-24s %s" % (p, r, region_cn(r)))
