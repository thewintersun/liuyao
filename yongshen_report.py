"""用神影子判定统计

用法：
    python yongshen_report.py            # 汇总全部
    python yongshen_report.py 14         # 只看最近 14 天
    python yongshen_report.py 14 --diff  # 并列出不一致的样本供人工核对

一致率高说明自动判定可以取代用户手选；不一致的样本要人工看是
判定错了还是用户选错了——两者都会出现，后者恰恰是撤掉选择页的理由。
"""

import sys
from collections import Counter

from dotenv import load_dotenv

load_dotenv()

from auth import get_db, release_db  # noqa: E402  需在 load_dotenv 之后导入

CHOICES = ('父母', '兄弟', '子孙', '妻财', '官鬼', '世爻')


def fetch(days=None):
    db = get_db()
    sql = 'SELECT * FROM yongshen_shadow'
    params = ()
    if days:
        sql += " WHERE created_at >= datetime('now', 'localtime', ?)"
        params = (f'-{int(days)} days',)
    sql += ' ORDER BY created_at DESC'
    rows = [dict(r) for r in db.execute(sql, params).fetchall()]
    release_db(db)
    return rows


def main():
    args = [a for a in sys.argv[1:]]
    show_diff = '--diff' in args
    days = next((int(a) for a in args if a.isdigit()), None)

    rows = fetch(days)
    if not rows:
        print('暂无影子判定记录。解卦跑起来后才会有数据。')
        return

    scope = f'最近 {days} 天' if days else '全部'
    print(f'=== 用神影子判定统计（{scope}，共 {len(rows)} 条）===\n')

    failed = [r for r in rows if r['llm_choice'] is None]
    ok = [r for r in rows if r['llm_choice'] is not None]
    print(f'判定成功 {len(ok)} 条，失败 {len(failed)} 条'
          f'（失败率 {100 * len(failed) / len(rows):.1f}%）')
    if failed:
        errs = Counter(str(r['error'])[:60] for r in failed).most_common(3)
        for msg, n in errs:
            print(f'    失败原因 x{n}: {msg}')

    comparable = [r for r in ok if r['agreed'] is not None]
    if comparable:
        agreed = sum(r['agreed'] for r in comparable)
        print(f'\n与用户所选一致：{agreed}/{len(comparable)}'
              f'  = {100 * agreed / len(comparable):.1f}%')

    times = [r['elapsed_ms'] for r in ok if r['elapsed_ms']]
    if times:
        times.sort()
        print(f'判定耗时：中位 {times[len(times) // 2]}ms，'
              f'最长 {times[-1]}ms')

    print('\n--- 用户所选 vs 系统判定（行=用户选，列=判定）---')
    matrix = Counter((r['user_choice'], r['llm_choice']) for r in comparable)
    users = sorted({r['user_choice'] for r in comparable})
    print('%-10s' % '' + ''.join('%-7s' % c for c in CHOICES))
    for u in users:
        row = '%-10s' % u
        for c in CHOICES:
            n = matrix.get((u, c), 0)
            row += '%-7s' % (n if n else '·')
        print(row)

    print('\n--- 判定结果分布 ---')
    for choice, n in Counter(r['llm_choice'] for r in ok).most_common():
        print(f'  {choice}  {n:4d}  {100 * n / len(ok):5.1f}%')

    if show_diff:
        diffs = [r for r in comparable if not r['agreed']]
        print(f'\n--- 不一致样本（{len(diffs)} 条）---')
        for r in diffs[:40]:
            print(f"\n  [{r['created_at']}] 用户选={r['user_choice']} 判定={r['llm_choice']}")
            print(f"    问题: {(r['question'] or '')[:70]}")
            print(f"    理由: {r['llm_reason']}")
        if len(diffs) > 40:
            print(f'\n  （还有 {len(diffs) - 40} 条未列出）')
    elif comparable:
        n = sum(1 for r in comparable if not r['agreed'])
        if n:
            print(f'\n有 {n} 条不一致，加 --diff 查看明细')


if __name__ == '__main__':
    main()
