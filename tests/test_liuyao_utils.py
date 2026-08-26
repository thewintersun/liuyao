"""六亲生克与用神/元神/忌神/仇神推导

这套关系是断卦的地基，错了会让每一次解卦的提示词都带错标注，
所以这里逐条钉死正统关系，不允许再被写反。
"""
import pytest

import copy
import json
import sqlite3

from liuyao_utils import (
    liuqin_sheng_mapping_dict as SHENG,
    liuqin_ke_mapping_dict as KE,
    get_yjc_pos_list,
    complete_liuqin,
    orgnize_data,
    liuqin_reverse_mapping_dict,
    SELF_DIVINATION,
)

# 正统六亲关系
TRUE_SHENG = {'父': '兄', '兄': '孙', '孙': '财', '财': '官', '官': '父'}
TRUE_KE = {'父': '孙', '孙': '官', '官': '兄', '兄': '财', '财': '父'}


class TestLiuqinRelations:
    @pytest.mark.parametrize('subject, target', TRUE_SHENG.items())
    def test_sheng(self, subject, target):
        """父母生兄弟、兄弟生子孙、子孙生妻财、妻财生官鬼、官鬼生父母"""
        assert SHENG[subject] == target

    @pytest.mark.parametrize('subject, target', TRUE_KE.items())
    def test_ke(self, subject, target):
        """父母克子孙、子孙克官鬼、官鬼克兄弟、兄弟克妻财、妻财克父母"""
        assert KE[subject] == target

    def test_ke_is_not_reverse_of_sheng(self):
        """克表不能是生表的反向——那是「谁生我」，曾导致忌神取成泄气之神"""
        reverse_sheng = {v: k for k, v in SHENG.items()}
        assert KE != reverse_sheng

    def test_both_tables_are_closed_cycles(self):
        """生与克都应是覆盖五种六亲的闭环，不重不漏"""
        for table in (SHENG, KE):
            assert set(table.keys()) == set('父兄孙财官')
            assert set(table.values()) == set('父兄孙财官')


# 泽水困卦的六亲排列，用于验证推导结果
ZESHUIKUN = ['财寅木', '父辰土', '官午火', '孙亥水', '兄酉金', '父未土']


class TestYuanJiChou:
    """元神＝生用神者，忌神＝克用神者，仇神＝克元神者"""

    def _names(self, positions):
        return [ZESHUIKUN[i] for i in positions]

    def test_yongshen_guanggui(self):
        yuan, ji, chou = get_yjc_pos_list(ZESHUIKUN, '官')
        assert self._names(yuan) == ['财寅木']          # 妻财生官鬼
        assert self._names(ji) == ['孙亥水']            # 子孙克官鬼
        assert self._names(chou) == ['兄酉金']          # 兄弟克元神妻财

    def test_yongshen_qicai(self):
        yuan, ji, chou = get_yjc_pos_list(ZESHUIKUN, '财')
        assert self._names(yuan) == ['孙亥水']                    # 子孙生妻财
        assert self._names(ji) == ['兄酉金']                      # 兄弟克妻财
        assert self._names(chou) == ['父辰土', '父未土']          # 父母克元神子孙

    @pytest.mark.parametrize('yongshen', ['父', '兄', '孙', '财', '官'])
    def test_yongshen_never_its_own_chou(self, yongshen):
        """用神不可能是自己的仇神——曾因克表写反而五种用神全部中招"""
        _, _, chou = get_yjc_pos_list(ZESHUIKUN, yongshen)
        assert not any(ZESHUIKUN[i][0] == yongshen for i in chou)

    @pytest.mark.parametrize('yongshen', ['父', '兄', '孙', '财', '官'])
    def test_yuanshen_and_jishen_never_overlap(self, yongshen):
        """同一爻不可能既生用神又克用神"""
        yuan, ji, _ = get_yjc_pos_list(ZESHUIKUN, yongshen)
        assert not (set(yuan) & set(ji))

    @pytest.mark.parametrize('yongshen', ['父', '兄', '孙', '财', '官'])
    def test_yongshen_is_neither_yuanshen_nor_jishen(self, yongshen):
        """用神自身既不生自己也不克自己"""
        yuan, ji, _ = get_yjc_pos_list(ZESHUIKUN, yongshen)
        for i in yuan + ji:
            assert ZESHUIKUN[i][0] != yongshen


class TestCompleteLiuqin:
    """补全六亲不得原地修改入参——入参常是 gua_xiang_info 里的列表，
    改坏了会跟着存进数据库，导致后续重建首条消息时崩在六亲首字上"""

    def test_completes_short_form(self):
        assert complete_liuqin(['父戌土', '孙亥水']) == ['父母戌土', '子孙亥水']

    def test_does_not_mutate_input(self):
        original = ['父戌土', '孙亥水', '财寅木']
        snapshot = list(original)
        complete_liuqin(original)
        assert original == snapshot

    def test_idempotent_on_full_form(self):
        """再跑一次不能补成「父母母戌土」"""
        once = complete_liuqin(['父戌土', '孙亥水'])
        assert complete_liuqin(once) == once

    def test_unknown_prefix_passes_through(self):
        assert complete_liuqin(['未知爻']) == ['未知爻']

    def test_empty_entries_do_not_crash(self):
        assert complete_liuqin(['', '父戌土', '']) == ['', '父母戌土', '']


# 一份最小可用的卦象数据，字段与顺序都取自真实结构。
# 注意六亲列表是「上爻 → 初爻」排列（排盘书写习惯，上爻在最上面），
# orgnize_data 内部会 reverse 成初爻在前再用。
SAMPLE_GUA = {
    'liushen': ['白虎', '玄武', '青龙', '朱雀', '勾陈', '腾蛇'],
    'maingua_liuqin': ['父未土', '兄酉金', '孙亥水', '官午火', '父辰土', '财寅木'],
    'biangua_liuqin': ['孙子水', '父戌土', '兄申金', '官午火', '父辰土', '财寅木'],
    'fugua_liuqin': ['父戌土', '兄申金', '官午火', '父辰土', '财寅木', '孙子水'],
    'dyao_display': ['3 动爻'],
    'timecn': ['丙午年丙申月辛未日丁酉时'],
    'time': ['2026年8月25日18时'],
    'kongwang': ['戌亥'],
    'shiyao_weizhi': ['0'],
    'yingyao_weizhi': ['3'],
    'maingua_gong': ['兑宫', '泽水困'],
    'biangua_gong': ['坎宫', '坎为水'],
    'maingua_youhun': [''],
    'biangua_youhun': [''],
    'maingua_liuchong': ['六合'],
    'biangua_liuchong': ['六冲'],
}


class TestOrgnizeDataPurity:
    """orgnize_data 不得改动传入的 gua_xiang_info：
    gua_app 在调用之后才把它原样存库，改坏会污染 conversations 表"""

    def _payload(self):
        return {
            'gua_xiang_info': copy.deepcopy(SAMPLE_GUA),
            'category': {'title': '官鬼', 'index': 1},
            'background': '',
        }

    def test_input_untouched(self):
        data = self._payload()
        before = copy.deepcopy(data['gua_xiang_info'])
        orgnize_data(data)
        assert data['gua_xiang_info'] == before

    def test_liuqin_order_and_form_preserved(self):
        """具体守住曾经被破坏的两点：顺序未被 reverse、六亲未被全称化"""
        data = self._payload()
        orgnize_data(data)
        assert data['gua_xiang_info']['maingua_liuqin'] == SAMPLE_GUA['maingua_liuqin']

    def test_output_still_correct(self):
        """净化输入的同时，产出的提示词内容不能变"""
        out = orgnize_data(self._payload())
        assert '主卦：泽水困卦' in out
        assert '子孙亥水' in out          # 输出仍是全称
        assert '用神为第3爻' in out

    def test_repeatable(self):
        """同一份数据连跑两次结果一致——原地修改时第二次会崩或产出脏数据"""
        data = self._payload()
        assert orgnize_data(data) == orgnize_data(data)


class TestSelfDivination:
    """自占自身以世爻为用神。曾映射到兄弟爻——兄弟代表同辈与竞争者，
    不能代表求测者本人；而这一项还是分类页的默认值，占实际用量一成以上"""

    def _run(self, category, shiyao_index):
        gua = copy.deepcopy(SAMPLE_GUA)
        gua['shiyao_weizhi'] = [str(shiyao_index)]
        return orgnize_data({
            'gua_xiang_info': gua,
            'category': {'title': category},
            'background': '',
        })

    def test_not_in_liuqin_table(self):
        """不应再留在六亲映射表里，避免被误用回兄弟爻"""
        assert SELF_DIVINATION not in liuqin_reverse_mapping_dict

    @pytest.mark.parametrize('shiyao_index, expect_yao', [(0, 1), (2, 3), (5, 6)])
    def test_takes_world_yao(self, shiyao_index, expect_yao):
        out = self._run(SELF_DIVINATION, shiyao_index)
        assert '自占自身，取世爻第%d爻' % expect_yao in out

    @pytest.mark.parametrize('shiyao_index', [0, 2, 5])
    def test_yongshen_and_world_yao_same_line(self, shiyao_index):
        """用神标注与世爻标注必须落在同一爻"""
        out = self._run(SELF_DIVINATION, shiyao_index)
        for line in out.split(chr(10)):
            if '为世爻' in line:
                assert '为用神' in line
                return
        pytest.fail('未找到世爻标注')

    def test_world_yao_is_not_forced_to_xiongdi(self):
        """世爻是父母爻时，用神就该是父母爻，不能还取兄弟"""
        out = self._run(SELF_DIVINATION, 0)   # SAMPLE_GUA reverse 后初爻为 财寅木
        assert '取世爻第1爻:妻财寅木' in out

    def test_other_categories_unaffected(self):
        """非自占类别仍按六亲映射取用神"""
        out = self._run('官鬼', 0)
        assert '自占自身' not in out
        assert '用神为第' in out
