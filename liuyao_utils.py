import copy



liuqin_sheng_mapping_dict = {
    '父': '兄',
    '兄': '孙',
    '孙': '财',
    '财': '官',
    '官': '父'
}
# 六亲相克：父母克子孙、子孙克官鬼、官鬼克兄弟、兄弟克妻财、妻财克父母。
# 注意不要写成生表的反向（那是「谁生我」），否则忌神会取成泄气之神、
# 仇神会取成用神自己。
liuqin_ke_mapping_dict = {
    '父': '孙',
    '孙': '官',
    '官': '兄',
    '兄': '财',
    '财': '父'
}

liuqin_mapping_dict = {
    '父': '父母',
    '兄': '兄弟',
    '官': '官鬼',
    '财': '妻财',
    '孙': '子孙'
}
# 「自占自身」不在此表中：自占以世爻为用神，由 orgnize_data 单独分支处理。
# 曾把它映射到兄弟爻，但兄弟代表的是同辈与竞争者，不能代表求测者本人。
SELF_DIVINATION = '自占自身'

liuqin_reverse_mapping_dict = {
    '父母': '父',
    '兄弟': '兄',
    '官鬼': '官',
    '妻财': '财',
    '子孙': '孙',
}

chong_mapping_dict = {
    "子": "午",
    "午": "子",
    "丑": "未",
    "未": "丑",
    "寅": "申",
    "申": "寅",
    "卯": "酉",
    "酉": "卯",
    "辰": "戌",
    "戌": "辰",
    "巳": "亥",
    "亥": "巳",
}

he_mapping_dict = {
    '子': '丑',
    '丑': '子',
    '寅': '亥',
    '亥': '寅',
    '卯': '戌',
    '戌': '卯',
    '辰': '酉',
    '酉': '辰',
    '巳': '申',
    '申': '巳',
    '午': '未',
    '未': '午',
}

sanhe_mapping_dict = {
    "申": "申子辰",
    "子": "申子辰",
    "辰": "申子辰",
    "巳": "巳酉丑",
    "酉": "巳酉丑",
    "丑": "巳酉丑",
    "戌": "寅午戌",
    "寅": "寅午戌",
    "午": "寅午戌",
    "亥": "亥卯未",
    "卯": "亥卯未",
    "未": "亥卯未",
}

#补全爻中六亲的说法，比如：父戌土，补全为父母戌土
#返回新列表而不原地修改：入参往往是 gua_xiang_info 里的列表，改坏了会连带存库的数据。
#对已是全称的输入保持幂等，否则再跑一次会补成「父母母戌土」。
def complete_liuqin(liuqin):
    full_names = set(liuqin_mapping_dict.values())
    result = []
    for item in liuqin:
        if item[:2] in full_names:
            result.append(item)
        elif item and item[0] in liuqin_mapping_dict:
            result.append(liuqin_mapping_dict[item[0]] + item[1:])
        else:
            result.append(item)
    return result

# 将字符串中的简短六亲补全，比如：父，补全为父母
def complete_liuqin_str(liuqin_str):
    for key in liuqin_mapping_dict:
        liuqin_str = liuqin_str.replace(key, liuqin_mapping_dict[key], -1)  # -1表示替换所有匹配项
    return liuqin_str

def get_yongshen_str(main_gua_liuqin,
                     fugua_liuqin,
                     dyao_display,
                     month_dizhi,
                     day_dizhi,
                     xun_kong_dizhi,
                     shiyao_weizhi,
                     yingyao_weizhi,
                     yongshen_char
                     ):

    yongshen_description = ''
    pos = []
    yongshen_pos = -1
    for i in range(len(main_gua_liuqin)):
        if yongshen_char == main_gua_liuqin[i][0]:
            pos.append(i)

    if len(pos) == 0:
        for i in range(len(fugua_liuqin)):
            if yongshen_char == fugua_liuqin[i][0]:
                yongshen_description = "用神不现，取伏神第" + str(i+1) + "爻:" + fugua_liuqin[i] + "为用神"
                yongshen_description += "，伏于主卦第" + str(i+1) + "爻" + main_gua_liuqin[i] + "之下。"
                return 0, i, yongshen_description

    if len(pos) == 1:
        yongshen_pos = pos[0]


    if len(pos) == 2:
        dyao_pos_list = []
        for i in range(len(dyao_display)):
            dyao_pos_list.append(int(dyao_display[i].split(' ')[0]))

        if (pos[0] in dyao_pos_list and pos[1] not in dyao_pos_list) or (pos[0] not in dyao_pos_list and pos[1] in dyao_pos_list):
            if pos[0] in dyao_pos_list:
                yongshen_pos = pos[0]
            else:
                yongshen_pos = pos[1]
        else:
            yongshen_dizhi_pos_0 = main_gua_liuqin[pos[0]][1]
            yongshen_dizhi_pos_1 = main_gua_liuqin[pos[1]][1]

            if yongshen_dizhi_pos_0 in xun_kong_dizhi and main_gua_liuqin[pos[1]][1] not in xun_kong_dizhi:
                yongshen_pos = pos[0]
            elif yongshen_dizhi_pos_0 not in xun_kong_dizhi and main_gua_liuqin[pos[1]][1] in xun_kong_dizhi:
                yongshen_pos = pos[1]
            else:
                yuepo = chong_mapping_dict[month_dizhi]
                if yongshen_dizhi_pos_0 == yuepo and yongshen_dizhi_pos_1 != yuepo:
                    yongshen_pos = pos[0]
                elif yongshen_dizhi_pos_0 != yuepo and yongshen_dizhi_pos_1 == yuepo:
                    yongshen_pos = pos[1]
                else:
                    if yongshen_dizhi_pos_0 == he_mapping_dict[day_dizhi] and yongshen_dizhi_pos_1 != he_mapping_dict[day_dizhi]:
                        yongshen_pos = pos[0]
                    elif yongshen_dizhi_pos_0 != he_mapping_dict[day_dizhi] and yongshen_dizhi_pos_1 == he_mapping_dict[day_dizhi]:
                        yongshen_pos = pos[1]
                    else:
                        if yongshen_dizhi_pos_0 in sanhe_mapping_dict[day_dizhi] and yongshen_dizhi_pos_1 not in sanhe_mapping_dict[day_dizhi]:
                            yongshen_pos = pos[0]
                        elif yongshen_dizhi_pos_0 not in sanhe_mapping_dict[day_dizhi] and yongshen_dizhi_pos_1 in sanhe_mapping_dict[day_dizhi]:
                            yongshen_pos = pos[1]
                        else:
                            if yongshen_dizhi_pos_0 == chong_mapping_dict[day_dizhi] and yongshen_dizhi_pos_1 != chong_mapping_dict[day_dizhi]:
                                yongshen_pos = pos[0]
                            elif yongshen_dizhi_pos_0 != chong_mapping_dict[day_dizhi] and yongshen_dizhi_pos_1 == chong_mapping_dict[day_dizhi]:
                                yongshen_pos = pos[1]
                            else:
                                if yongshen_dizhi_pos_0 == he_mapping_dict[month_dizhi] and yongshen_dizhi_pos_1 != he_mapping_dict[month_dizhi]:
                                    yongshen_pos = pos[0]
                                elif yongshen_dizhi_pos_0 != he_mapping_dict[month_dizhi] and yongshen_dizhi_pos_1 == he_mapping_dict[month_dizhi]:
                                    yongshen_pos = pos[1]
                                else:
                                    dyao_chong_list = []
                                    dyao_he_list = []
                                    for i in dyao_pos_list:
                                        dyao_chong_list.append(chong_mapping_dict[main_gua_liuqin[i][1]])
                                        dyao_he_list.append(he_mapping_dict[main_gua_liuqin[i][1]])

                                    if yongshen_dizhi_pos_0 in dyao_he_list and yongshen_dizhi_pos_1 not in dyao_he_list:
                                        yongshen_pos = pos[0]
                                    elif yongshen_dizhi_pos_0 not in dyao_he_list and yongshen_dizhi_pos_1 in dyao_he_list:
                                        yongshen_pos = pos[1]
                                    else:
                                        if yongshen_dizhi_pos_0 in dyao_chong_list and yongshen_dizhi_pos_1 not in dyao_chong_list:
                                            yongshen_pos = pos[0]
                                        elif yongshen_dizhi_pos_0 not in dyao_chong_list and yongshen_dizhi_pos_1 in dyao_chong_list:
                                            yongshen_pos = pos[1]
                                        else:
                                            shiyingyao_pos_list = [int(shiyao_weizhi[0]), int(yingyao_weizhi[0])]
                                            if pos[0] in shiyingyao_pos_list and pos[1] not in shiyingyao_pos_list:
                                                yongshen_pos = pos[0]
                                            elif pos[0] not in shiyingyao_pos_list and pos[1] in shiyingyao_pos_list:
                                                yongshen_pos = pos[1]
                                            else:
                                                if pos[0] in shiyingyao_pos_list and pos[1] in shiyingyao_pos_list:
                                                    yongshen_pos = pos[0]
                                                else:
                                                    shi_ying_distance_0 = min(abs(pos[0] - int(shiyao_weizhi[0])), abs(pos[0] - int(yingyao_weizhi[0])))
                                                    shi_ying_distance_1 = min(abs(pos[1] - int(shiyao_weizhi[0])), abs(pos[1] - int(yingyao_weizhi[0])))
                                                    if shi_ying_distance_0 < shi_ying_distance_1:
                                                        yongshen_pos = pos[0]
                                                    elif shi_ying_distance_0 > shi_ying_distance_1:
                                                        yongshen_pos = pos[1]
                                                    else:
                                                        shi_distance_0 = abs(pos[0] - int(shiyao_weizhi[0]))
                                                        shi_distance_1 = abs(pos[1] - int(shiyao_weizhi[0]))
                                                        if shi_distance_0 < shi_distance_1:
                                                            yongshen_pos = pos[0]
                                                        elif shi_distance_0 > shi_distance_1:
                                                            yongshen_pos = pos[1]
                                                        else:
                                                            yongshen_pos = min(pos[0], pos[1])
    yongshen_description = "用神为第" + str(yongshen_pos + 1) + "爻:" + main_gua_liuqin[yongshen_pos] + "。"
    return 1, yongshen_pos, yongshen_description


def get_yjc_pos_list(main_gua_liuqin, yongshen_char):
    yuanshen_pos_list = []
    jishen_pos_list = []
    choushen_pos_list = []

    yuanshen_char = ''
    for ls in liuqin_sheng_mapping_dict:
        if liuqin_sheng_mapping_dict[ls] == yongshen_char:
            yuanshen_char = ls
            break
    for i in range(len(main_gua_liuqin)):
        if liuqin_sheng_mapping_dict[main_gua_liuqin[i][0]] == yongshen_char:
            yuanshen_pos_list.append(i)
        if liuqin_ke_mapping_dict[main_gua_liuqin[i][0]] == yongshen_char:
            jishen_pos_list.append(i)
        if liuqin_ke_mapping_dict[main_gua_liuqin[i][0]] == yuanshen_char:
            choushen_pos_list.append(i)

    return yuanshen_pos_list, jishen_pos_list, choushen_pos_list

def orgnize_data(data):
    # 深拷贝：下面会 reverse 六亲列表，不能改到调用方的 gua_xiang_info——
    # 它随后要原样存库，被改坏会导致重建首条消息时崩在六亲首字上
    gua_xiang_info = copy.deepcopy(data['gua_xiang_info'])
    background_text = data['background']
    category_title = data['category']['title']

    liushen = gua_xiang_info['liushen']
    fugua_liuqin = gua_xiang_info['fugua_liuqin']
    maingua_liuqin = gua_xiang_info['maingua_liuqin']
    biangua_liuqin = gua_xiang_info['biangua_liuqin']
    fugua_liuqin.reverse()
    maingua_liuqin.reverse()
    biangua_liuqin.reverse()

    dyao_display = gua_xiang_info['dyao_display']

    month_dizhi = gua_xiang_info['timecn'][0][4]
    day_dizhi = gua_xiang_info['timecn'][0][7]
    xun_kong_dizhi = gua_xiang_info['kongwang']

    shiyao_weizhi = gua_xiang_info['shiyao_weizhi']
    yingyao_weizhi = gua_xiang_info['yingyao_weizhi']
    shiyao_weizhi_int = int(shiyao_weizhi[0])
    yingyao_weizhi_int = int(yingyao_weizhi[0])

    maingua_youhun = gua_xiang_info['maingua_youhun']
    biangua_youhun = gua_xiang_info['biangua_youhun']
    maingua_liuchong = gua_xiang_info['maingua_liuchong']
    biangua_liuchong = gua_xiang_info['biangua_liuchong']

    if category_title == SELF_DIVINATION:
        # 自占自身以世爻为用神。shiyao_weizhi 的索引基准是 reverse 之后的
        # maingua_liuqin（0 为初爻），此处可直接索引。
        # 元神/忌神/仇神仍按世爻实际所属六亲推算。
        ys_is_main = 1
        ys_pos = shiyao_weizhi_int
        yongshen_char = maingua_liuqin[ys_pos][0]
        yongshen_description = "自占自身，取世爻第" + str(ys_pos + 1) + "爻:" + maingua_liuqin[ys_pos] + "为用神。"
    else:
        yongshen_char = liuqin_reverse_mapping_dict[category_title]
        ys_is_main, ys_pos, yongshen_description = get_yongshen_str(maingua_liuqin,
                                            fugua_liuqin,
                                            dyao_display,
                                            month_dizhi,
                                            day_dizhi,
                                            xun_kong_dizhi,
                                            shiyao_weizhi,
                                            yingyao_weizhi,
                                            yongshen_char)
    yongshen_description = complete_liuqin_str(yongshen_description)

    yuanshen_pos_list, jishen_pos_list, choushen_pos_list = get_yjc_pos_list(maingua_liuqin, yongshen_char)
    maingua_liuqin = complete_liuqin(maingua_liuqin)
    biangua_liuqin = complete_liuqin(biangua_liuqin)
    fugua_liuqin = complete_liuqin(fugua_liuqin)

    dyao_pos_list = []
    for i in range(len(dyao_display)):
        dyao_pos_list.append(int(dyao_display[i].split(' ')[0]))
    date_description = "公历时间：" + gua_xiang_info['time'][0] + "。"
    datecn_description = "时间干支：" + gua_xiang_info['timecn'][0] + "。"

    main_gua_description = "主卦：" + gua_xiang_info['maingua_gong'][1] + "卦,属于" + gua_xiang_info['maingua_gong'][0]
    if len(maingua_youhun) > 0 and len(maingua_youhun[0]) > 0:
        main_gua_description += "," + maingua_youhun[0]
    if len(maingua_liuchong) > 0 and len(maingua_liuchong[0]) > 0:
        main_gua_description += "," + maingua_liuchong[0] + "卦"

    main_gua_description += "。"
    biangua_description = "变卦：" + gua_xiang_info['biangua_gong'][1] + "卦,属于" + gua_xiang_info['biangua_gong'][0]
    if len(biangua_youhun) > 0 and len(biangua_youhun[0]) > 0:
        biangua_description += "," + biangua_youhun[0]
    if len(biangua_liuchong) > 0 and len(biangua_liuchong[0]) > 0:
        biangua_description += "," + biangua_liuchong[0] + "卦"
    biangua_description += "。"

    main_gua_yaoci_description = "主卦爻信息：\n"
    for i in range(len(maingua_liuqin)):
        main_gua_yaoci_description += "第" + str(i+1) + "爻：" + maingua_liuqin[i]
        main_gua_yaoci_description += ",六神是" + liushen[i]

        if ys_is_main == 1 and i == ys_pos:
            main_gua_yaoci_description += ",为用神,"
        if ys_is_main == 0 and i == ys_pos:
            main_gua_yaoci_description += ",为飞神,用神伏于此爻之下。用神为伏神:" + fugua_liuqin[i]

        if i in yuanshen_pos_list:
            main_gua_yaoci_description += ",为元神"
        if i in jishen_pos_list:
            main_gua_yaoci_description += ",为忌神"
        if i in choushen_pos_list:
            main_gua_yaoci_description += ",为仇神"

        if i == shiyao_weizhi_int:
            main_gua_yaoci_description += ",为世爻"
        elif i == yingyao_weizhi_int:
            main_gua_yaoci_description += ",为应爻"

        if i in dyao_pos_list:
            main_gua_yaoci_description += ",为动爻,发动化变爻:" + biangua_liuqin[i]
        main_gua_yaoci_description += ";\n"

    biangua_yaoci_description = "变卦爻信息：\n"
    for i in range(len(biangua_liuqin)):
        biangua_yaoci_description += "第" + str(i+1) + "爻：" + biangua_liuqin[i] + ";\n"

    fugua_yaoci_description = ""
    if ys_is_main == 0:
        fugua_yaoci_description = "伏神爻信息：\n"
        fugua_yaoci_description += "伏神第" + str(ys_pos+1) + "爻：" + fugua_liuqin[ys_pos] + \
                                    "为用神，伏于飞神主卦第" + str(ys_pos+1) + "爻" + maingua_liuqin[ys_pos] + "之下。\n"

    all_description = date_description + "\n" + datecn_description + "\n" + main_gua_description + "\n" + biangua_description + "\n" + \
                 main_gua_yaoci_description + "\n" + biangua_yaoci_description + "\n" + fugua_yaoci_description + "\n" + yongshen_description + "\n"

    additional_description = ""
    if len(background_text) > 0:
        additional_description = "所求之事：" + background_text + "\n"

    all_description += additional_description

    return all_description
