"""Генерирует passport-chaikagrad.docx — два паспорта на листе A4."""

from docx import Document
from docx.shared import Cm, Pt, RGBColor, Mm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

NAVY  = RGBColor(0x0D, 0x2D, 0x5E)
GRAY  = RGBColor(0xAA, 0xAA, 0xAA)
LGRAY = RGBColor(0xCC, 0xCC, 0xCC)
DGRAY = RGBColor(0x66, 0x66, 0x66)

# ──────────────────────────────────────────────────────────────
# Низкоуровневые хелперы
# ──────────────────────────────────────────────────────────────

def _tcBorders(cell, top=None, bottom=None, left=None, right=None):
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    # удалим старые border-элементы
    for old in tcPr.findall(qn('w:tcBorders')):
        tcPr.remove(old)
    bEl = OxmlElement('w:tcBorders')
    for side, cfg in [('top', top), ('bottom', bottom),
                      ('left', left), ('right', right)]:
        if cfg:
            el = OxmlElement(f'w:{side}')
            el.set(qn('w:val'),   cfg.get('val',   'single'))
            el.set(qn('w:sz'),    str(cfg.get('sz', 4)))
            el.set(qn('w:space'), '0')
            el.set(qn('w:color'), cfg.get('color', '000000'))
            bEl.append(el)
    tcPr.append(bEl)


def no_border(cell):
    _tcBorders(cell,
               top   ={'val': 'none'},
               bottom={'val': 'none'},
               left  ={'val': 'none'},
               right ={'val': 'none'})


def underline_border(cell, color='555555', sz=4):
    _tcBorders(cell,
               top   ={'val': 'none'},
               bottom={'val': 'single', 'sz': sz, 'color': color},
               left  ={'val': 'none'},
               right ={'val': 'none'})


def box_border(cell, color='0D2D5E', sz=8):
    _tcBorders(cell,
               top   ={'val': 'single', 'sz': sz, 'color': color},
               bottom={'val': 'single', 'sz': sz, 'color': color},
               left  ={'val': 'single', 'sz': sz, 'color': color},
               right ={'val': 'single', 'sz': sz, 'color': color})


def set_row_height(row, height_mm, rule='exact'):
    trPr = row._tr.get_or_add_trPr()
    for old in trPr.findall(qn('w:trHeight')):
        trPr.remove(old)
    h = OxmlElement('w:trHeight')
    h.set(qn('w:val'), str(int(Mm(height_mm).emu / 914)))
    h.set(qn('w:hRule'), rule)
    trPr.append(h)


def set_cell_bg(cell, hex6):
    tcPr = cell._tc.get_or_add_tcPr()
    shd  = OxmlElement('w:shd')
    shd.set(qn('w:val'),   'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'),  hex6)
    tcPr.append(shd)


def add_para_border_bottom(para, color='0D2D5E', sz=4):
    pPr  = para._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bot  = OxmlElement('w:bottom')
    bot.set(qn('w:val'),   'single')
    bot.set(qn('w:sz'),    str(sz))
    bot.set(qn('w:space'), '1')
    bot.set(qn('w:color'), color)
    pBdr.append(bot)
    pPr.append(pBdr)


def labeled_run(cell, text, size=6, color=NAVY, bold=False,
                align=WD_ALIGN_PARAGRAPH.LEFT,
                space_before=0, space_after=0):
    p = cell.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after  = Pt(space_after)
    r = p.add_run(text)
    r.font.size     = Pt(size)
    r.font.color.rgb = color
    r.font.bold     = bold
    return p


# ──────────────────────────────────────────────────────────────
# Левая страница паспорта (фото + ФИО + адрес + подписи)
# ──────────────────────────────────────────────────────────────

def build_left(cell):
    cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP

    # Заголовок
    hp = labeled_run(cell, 'ЧАЙКАГРАД  ·  ЛИЧНЫЕ СВЕДЕНИЯ',
                     size=6, bold=True, color=NAVY,
                     align=WD_ALIGN_PARAGRAPH.CENTER,
                     space_before=3, space_after=2)
    add_para_border_bottom(hp)

    # ── Блок: фото слева + ФИО справа ─────────────────────────
    t = cell.add_table(rows=1, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    photo_c = t.rows[0].cells[0]
    fio_c   = t.rows[0].cells[1]
    photo_c.width = Cm(3.2)
    fio_c.width   = Cm(6.3)
    no_border(photo_c)
    no_border(fio_c)

    # Рамка фото
    pt = photo_c.add_table(rows=1, cols=1)
    ph = pt.rows[0].cells[0]
    ph.width = Cm(2.8)
    box_border(ph, sz=6)
    set_row_height(pt.rows[0], 36)
    fp = ph.add_paragraph('ФОТО')
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fp.paragraph_format.space_before = Pt(22)
    fp.paragraph_format.space_after  = Pt(0)
    fp.runs[0].font.size      = Pt(6.5)
    fp.runs[0].font.color.rgb = LGRAY

    # Поля ФИО
    for label in ('Фамилия', 'Имя', 'Отчество', 'Дата рождения'):
        ft = fio_c.add_table(rows=1, cols=2)
        lc = ft.rows[0].cells[0]
        vc = ft.rows[0].cells[1]
        lc.width = Cm(2.5)
        vc.width = Cm(3.7)
        no_border(lc)
        underline_border(vc)
        lp = lc.add_paragraph(label)
        lp.paragraph_format.space_before = Pt(1)
        lp.paragraph_format.space_after  = Pt(0)
        lp.runs[0].font.size      = Pt(5.5)
        lp.runs[0].font.color.rgb = NAVY
        vp = vc.add_paragraph('')
        vp.paragraph_format.space_before = Pt(1)
        vp.paragraph_format.space_after  = Pt(2)

    # ── Место жительства ──────────────────────────────────────
    ap = labeled_run(cell, 'МЕСТО ЖИТЕЛЬСТВА',
                     size=5.5, bold=True, color=NAVY, space_before=4, space_after=1)
    for _ in range(2):
        at = cell.add_table(rows=1, cols=1)
        ac = at.rows[0].cells[0]
        ac.width = Cm(9.6)
        no_border(ac)
        underline_border(ac)
        p = ac.add_paragraph('')
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after  = Pt(2)

    # ── Отряд ────────────────────────────────────────────────
    sq = cell.add_table(rows=1, cols=2)
    slc = sq.rows[0].cells[0]
    svc = sq.rows[0].cells[1]
    slc.width = Cm(1.8)
    svc.width = Cm(7.7)
    no_border(slc)
    underline_border(svc)
    sp = slc.add_paragraph('Отряд')
    sp.paragraph_format.space_before = Pt(4)
    sp.paragraph_format.space_after  = Pt(0)
    sp.runs[0].font.size      = Pt(5.5)
    sp.runs[0].font.color.rgb = NAVY
    svp = svc.add_paragraph('')
    svp.paragraph_format.space_before = Pt(4)
    svp.paragraph_format.space_after  = Pt(1)

    # ── Подписи ───────────────────────────────────────────────
    divp = cell.add_paragraph()
    divp.paragraph_format.space_before = Pt(6)
    divp.paragraph_format.space_after  = Pt(1)
    pPr  = divp._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    top  = OxmlElement('w:top')
    top.set(qn('w:val'), 'single'); top.set(qn('w:sz'), '2')
    top.set(qn('w:space'), '1');    top.set(qn('w:color'), 'CCCCCC')
    pBdr.append(top); pPr.append(pBdr)

    sig = cell.add_table(rows=3, cols=2)
    for ci, label in enumerate(['Подпись гражданина', 'Подпись директора']):
        lc2 = sig.rows[0].cells[ci]
        vc2 = sig.rows[1].cells[ci]
        nc  = sig.rows[2].cells[ci]
        no_border(lc2); underline_border(vc2); no_border(nc)
        lp2 = lc2.add_paragraph(label)
        lp2.paragraph_format.space_before = Pt(0)
        lp2.paragraph_format.space_after  = Pt(0)
        lp2.runs[0].font.size      = Pt(5.5)
        lp2.runs[0].font.color.rgb = NAVY
        set_row_height(sig.rows[1], 10)
        vp2 = vc2.add_paragraph('')
        vp2.paragraph_format.space_before = Pt(0)
        vp2.paragraph_format.space_after  = Pt(0)
        np_ = nc.add_paragraph('(подпись)')
        np_.alignment = WD_ALIGN_PARAGRAPH.CENTER
        np_.paragraph_format.space_before = Pt(0)
        np_.paragraph_format.space_after  = Pt(0)
        np_.runs[0].font.size      = Pt(5)
        np_.runs[0].font.color.rgb = LGRAY


# ──────────────────────────────────────────────────────────────
# Правая страница паспорта (достижения)
# ──────────────────────────────────────────────────────────────

def build_right(cell):
    cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP

    hp = labeled_run(cell, 'ЧАЙКАГРАД  ·  ДОСТИЖЕНИЯ',
                     size=6, bold=True, color=NAVY,
                     align=WD_ALIGN_PARAGRAPH.CENTER,
                     space_before=3, space_after=2)
    add_para_border_bottom(hp)

    for i in range(1, 7):
        rt = cell.add_table(rows=1, cols=3)
        nc  = rt.rows[0].cells[0]   # номер
        lc  = rt.rows[0].cells[1]   # строки
        stc = rt.rows[0].cells[2]   # печать

        nc.width  = Cm(0.55)
        lc.width  = Cm(8.0)
        stc.width = Cm(1.2)
        no_border(nc); no_border(lc); no_border(stc)

        np_ = nc.add_paragraph(f'{i}.')
        np_.paragraph_format.space_before = Pt(3)
        np_.paragraph_format.space_after  = Pt(0)
        np_.runs[0].font.size      = Pt(7)
        np_.runs[0].font.color.rgb = NAVY
        np_.runs[0].font.bold      = True

        # 2 строки для записи достижения
        inner = lc.add_table(rows=2, cols=1)
        for r in inner.rows:
            rc = r.cells[0]
            no_border(rc)
            underline_border(rc, color='BBBBBB', sz=2)
            rp = rc.add_paragraph('')
            rp.paragraph_format.space_before = Pt(1)
            rp.paragraph_format.space_after  = Pt(2)

        # Кружок-печать
        sp = stc.add_paragraph('◯')
        sp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        sp.paragraph_format.space_before = Pt(2)
        sp.paragraph_format.space_after  = Pt(0)
        sp.runs[0].font.size      = Pt(18)
        sp.runs[0].font.color.rgb = LGRAY

        # Зазор
        gap = cell.add_paragraph()
        gap.paragraph_format.space_before = Pt(0)
        gap.paragraph_format.space_after  = Pt(1)


# ──────────────────────────────────────────────────────────────
# Один паспорт (левая + правая страница)
# ──────────────────────────────────────────────────────────────

def build_passport(container_cell):
    container_cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP

    spread = container_cell.add_table(rows=1, cols=2)
    spread.alignment = WD_TABLE_ALIGNMENT.CENTER

    lc = spread.rows[0].cells[0]
    rc = spread.rows[0].cells[1]
    lc.width = Cm(9.8)
    rc.width = Cm(9.8)
    box_border(lc, sz=6)
    box_border(rc, sz=6)

    lc.width = Cm(9.8)
    rc.width = Cm(9.8)

    build_left(lc)
    build_right(rc)


# ──────────────────────────────────────────────────────────────
# Главный документ
# ──────────────────────────────────────────────────────────────

def make_doc():
    doc = Document()

    section = doc.sections[0]
    section.page_width    = Mm(210)
    section.page_height   = Mm(297)
    section.left_margin   = Mm(7)
    section.right_margin  = Mm(7)
    section.top_margin    = Mm(5)
    section.bottom_margin = Mm(5)

    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.paragraph_format.space_before = Pt(0)
    style.paragraph_format.space_after  = Pt(0)

    # Контейнер: строка 0 — паспорт 1, строка 1 — разделитель, строка 2 — паспорт 2
    tbl = doc.add_table(rows=3, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER

    for row in tbl.rows:
        c = row.cells[0]
        c.width = Mm(196)
        no_border(c)

    # Паспорт 1
    build_passport(tbl.rows[0].cells[0])

    # Разделитель
    sep_c = tbl.rows[1].cells[0]
    no_border(sep_c)
    sep_p = sep_c.add_paragraph(
        '- - - - - - - - - - - - - - - - - - - - ✂ разрезать ✂ - - - - - - - - - - - - - - - - - - - -'
    )
    sep_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sep_p.paragraph_format.space_before = Pt(3)
    sep_p.paragraph_format.space_after  = Pt(3)
    sep_p.runs[0].font.size      = Pt(6)
    sep_p.runs[0].font.color.rgb = DGRAY

    # Паспорт 2
    build_passport(tbl.rows[2].cells[0])

    out = '/home/user/kti-support-bot/passport-chaikagrad.docx'
    doc.save(out)
    print(f'Сохранено: {out}')


if __name__ == '__main__':
    make_doc()
