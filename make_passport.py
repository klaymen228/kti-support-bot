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
# Хелперы
# ──────────────────────────────────────────────────────────────

def _tc_borders(cell, top=None, bottom=None, left=None, right=None):
    tcPr = cell._tc.get_or_add_tcPr()
    for old in tcPr.findall(qn('w:tcBorders')):
        tcPr.remove(old)
    bEl = OxmlElement('w:tcBorders')
    for side, cfg in [('top', top), ('bottom', bottom),
                      ('left', left), ('right', right)]:
        if cfg:
            el = OxmlElement(f'w:{side}')
            el.set(qn('w:val'),   cfg.get('val', 'single'))
            el.set(qn('w:sz'),    str(cfg.get('sz', 4)))
            el.set(qn('w:space'), '0')
            el.set(qn('w:color'), cfg.get('color', '000000'))
            bEl.append(el)
    tcPr.append(bEl)


def no_border(cell):
    _tc_borders(cell,
                top={'val': 'none'}, bottom={'val': 'none'},
                left={'val': 'none'}, right={'val': 'none'})


def underline(cell, color='444444', sz=6):
    _tc_borders(cell,
                top={'val': 'none'}, bottom={'val': 'single', 'sz': sz, 'color': color},
                left={'val': 'none'}, right={'val': 'none'})


def box(cell, color='0D2D5E', sz=10):
    _tc_borders(cell,
                top={'val': 'single', 'sz': sz, 'color': color},
                bottom={'val': 'single', 'sz': sz, 'color': color},
                left={'val': 'single', 'sz': sz, 'color': color},
                right={'val': 'single', 'sz': sz, 'color': color})


def set_row_h(row, mm, rule='exact'):
    trPr = row._tr.get_or_add_trPr()
    for old in trPr.findall(qn('w:trHeight')):
        trPr.remove(old)
    h = OxmlElement('w:trHeight')
    h.set(qn('w:val'), str(int(Mm(mm).emu / 914)))
    h.set(qn('w:hRule'), rule)
    trPr.append(h)


def p_border_bottom(para, color='0D2D5E', sz=4):
    pPr = para._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bot = OxmlElement('w:bottom')
    bot.set(qn('w:val'), 'single')
    bot.set(qn('w:sz'), str(sz))
    bot.set(qn('w:space'), '1')
    bot.set(qn('w:color'), color)
    pBdr.append(bot)
    pPr.append(pBdr)


def txt(cell, text='', size=7, bold=False, color=NAVY,
        align=WD_ALIGN_PARAGRAPH.LEFT, sb=0, sa=0):
    p = cell.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(sb)
    p.paragraph_format.space_after  = Pt(sa)
    r = p.add_run(text)
    r.font.size      = Pt(size)
    r.font.bold      = bold
    r.font.color.rgb = color
    return p


def field_row(parent_cell, label, label_w_cm, value_w_cm, sb=2, sa=1):
    """Строка: метка | подчёркнутое поле."""
    t = parent_cell.add_table(rows=1, cols=2)
    lc = t.rows[0].cells[0]
    vc = t.rows[0].cells[1]
    lc.width = Cm(label_w_cm)
    vc.width = Cm(value_w_cm)
    no_border(lc)
    underline(vc)
    lc.vertical_alignment = WD_ALIGN_VERTICAL.BOTTOM
    vc.vertical_alignment = WD_ALIGN_VERTICAL.BOTTOM
    lp = lc.add_paragraph(label)
    lp.paragraph_format.space_before = Pt(sb)
    lp.paragraph_format.space_after  = Pt(sa)
    lp.runs[0].font.size      = Pt(6)
    lp.runs[0].font.color.rgb = NAVY
    vp = vc.add_paragraph('')
    vp.paragraph_format.space_before = Pt(sb)
    vp.paragraph_format.space_after  = Pt(sa)


# ──────────────────────────────────────────────────────────────
# Левая страница: фото + ФИО + адрес + подписи
# ──────────────────────────────────────────────────────────────

def build_left(cell):
    cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP
    W = 9.6  # рабочая ширина страницы в cm

    # Заголовок
    h = txt(cell, 'ЧАЙКАГРАД  ·  ЛИЧНЫЕ СВЕДЕНИЯ',
            size=6.5, bold=True, color=NAVY,
            align=WD_ALIGN_PARAGRAPH.CENTER, sb=3, sa=3)
    p_border_bottom(h)

    # ── Главный блок: квадрат фото слева + поля справа ────────
    main = cell.add_table(rows=1, cols=2)
    main.alignment = WD_TABLE_ALIGNMENT.LEFT
    photo_cell = main.rows[0].cells[0]
    fio_cell   = main.rows[0].cells[1]

    PHOTO_W = 3.8
    FIO_W   = W - PHOTO_W - 0.3
    photo_cell.width = Cm(PHOTO_W)
    fio_cell.width   = Cm(FIO_W)
    no_border(photo_cell)
    no_border(fio_cell)
    photo_cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP
    fio_cell.vertical_alignment   = WD_ALIGN_VERTICAL.TOP

    # Квадрат фото — вложенная таблица 1×1
    pt = photo_cell.add_table(rows=1, cols=1)
    ph = pt.rows[0].cells[0]
    ph.width = Cm(PHOTO_W - 0.2)
    box(ph, sz=12)
    set_row_h(pt.rows[0], 44)   # ~44 мм — ощутимый квадрат
    ph.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    fp = ph.add_paragraph('ФОТО')
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fp.paragraph_format.space_before = Pt(0)
    fp.paragraph_format.space_after  = Pt(0)
    fp.runs[0].font.size      = Pt(8)
    fp.runs[0].font.color.rgb = LGRAY
    fp.runs[0].font.bold      = True

    # Поля ФИО справа от фото
    for label in ('Фамилия', 'Имя', 'Отчество', 'Дата рождения'):
        t = fio_cell.add_table(rows=1, cols=2)
        lc = t.rows[0].cells[0]
        vc = t.rows[0].cells[1]
        lc.width = Cm(2.8)
        vc.width = Cm(FIO_W - 2.9)
        no_border(lc); underline(vc)
        lc.vertical_alignment = WD_ALIGN_VERTICAL.BOTTOM
        vc.vertical_alignment = WD_ALIGN_VERTICAL.BOTTOM
        lp = lc.add_paragraph(label)
        lp.paragraph_format.space_before = Pt(3)
        lp.paragraph_format.space_after  = Pt(0)
        lp.runs[0].font.size      = Pt(5.5)
        lp.runs[0].font.color.rgb = NAVY
        vp = vc.add_paragraph('')
        vp.paragraph_format.space_before = Pt(3)
        vp.paragraph_format.space_after  = Pt(1)

    # ── Место жительства ──────────────────────────────────────
    al = txt(cell, 'МЕСТО ЖИТЕЛЬСТВА',
             size=5.5, bold=True, color=NAVY, sb=5, sa=1)

    for _ in range(2):
        at = cell.add_table(rows=1, cols=1)
        ac = at.rows[0].cells[0]
        ac.width = Cm(W)
        no_border(ac); underline(ac)
        ap = ac.add_paragraph('')
        ap.paragraph_format.space_before = Pt(1)
        ap.paragraph_format.space_after  = Pt(3)

    # ── Отряд ────────────────────────────────────────────────
    field_row(cell, 'Отряд', 1.6, W - 1.7, sb=4, sa=1)

    # ── Разделитель подписей ──────────────────────────────────
    div = cell.add_paragraph()
    div.paragraph_format.space_before = Pt(7)
    div.paragraph_format.space_after  = Pt(1)
    pPr  = div._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    top  = OxmlElement('w:top')
    top.set(qn('w:val'), 'single')
    top.set(qn('w:sz'), '2')
    top.set(qn('w:space'), '1')
    top.set(qn('w:color'), 'AAAAAA')
    pBdr.append(top); pPr.append(pBdr)

    # ── Подписи (2 колонки) ───────────────────────────────────
    sig = cell.add_table(rows=3, cols=2)
    for ci, label in enumerate(['Подпись гражданина', 'Подпись директора']):
        lc2 = sig.rows[0].cells[ci]
        vc2 = sig.rows[1].cells[ci]
        nc  = sig.rows[2].cells[ci]
        no_border(lc2); underline(vc2); no_border(nc)

        lp2 = lc2.add_paragraph(label)
        lp2.paragraph_format.space_before = Pt(0)
        lp2.paragraph_format.space_after  = Pt(0)
        lp2.runs[0].font.size      = Pt(5.5)
        lp2.runs[0].font.color.rgb = NAVY

        set_row_h(sig.rows[1], 11)
        vp2 = vc2.add_paragraph('')
        vp2.paragraph_format.space_before = Pt(0)
        vp2.paragraph_format.space_after  = Pt(0)

        np_ = nc.add_paragraph('(подпись)')
        np_.alignment = WD_ALIGN_PARAGRAPH.CENTER
        np_.paragraph_format.space_before = Pt(0)
        np_.paragraph_format.space_after  = Pt(2)
        np_.runs[0].font.size      = Pt(5)
        np_.runs[0].font.color.rgb = LGRAY


# ──────────────────────────────────────────────────────────────
# Правая страница: просто "ДОСТИЖЕНИЯ" + пустое поле
# ──────────────────────────────────────────────────────────────

def build_right(cell):
    cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP

    h = txt(cell, 'ЧАЙКАГРАД  ·  ДОСТИЖЕНИЯ',
            size=6.5, bold=True, color=NAVY,
            align=WD_ALIGN_PARAGRAPH.CENTER, sb=3, sa=3)
    p_border_bottom(h)

    # Пустое поле — вложенная таблица с рамкой
    empty = cell.add_table(rows=1, cols=1)
    ec = empty.rows[0].cells[0]
    ec.width = Cm(9.4)
    box(ec, color='CCCCCC', sz=4)
    set_row_h(empty.rows[0], 108, rule='atLeast')
    ec.vertical_alignment = WD_ALIGN_VERTICAL.TOP
    ep = ec.add_paragraph('')
    ep.paragraph_format.space_before = Pt(0)
    ep.paragraph_format.space_after  = Pt(0)


# ──────────────────────────────────────────────────────────────
# Один паспорт в ячейку контейнера
# ──────────────────────────────────────────────────────────────

def build_passport(container_cell):
    container_cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP

    spread = container_cell.add_table(rows=1, cols=2)
    spread.alignment = WD_TABLE_ALIGNMENT.CENTER

    lc = spread.rows[0].cells[0]
    rc = spread.rows[0].cells[1]
    lc.width = Cm(9.8)
    rc.width = Cm(9.8)
    box(lc, sz=6)
    box(rc, sz=6)

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

    # 3 строки: паспорт 1 | разделитель | паспорт 2
    tbl = doc.add_table(rows=3, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER

    for row in tbl.rows:
        no_border(row.cells[0])
        row.cells[0].width = Mm(196)

    build_passport(tbl.rows[0].cells[0])

    # Линия разреза
    sep_c = tbl.rows[1].cells[0]
    no_border(sep_c)
    sp = sep_c.add_paragraph(
        '- - - - - - - - - - - - - - - - - - - - - ✂  разрезать  ✂ - - - - - - - - - - - - - - - - - - - -'
    )
    sp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sp.paragraph_format.space_before = Pt(4)
    sp.paragraph_format.space_after  = Pt(4)
    sp.runs[0].font.size      = Pt(6)
    sp.runs[0].font.color.rgb = DGRAY

    build_passport(tbl.rows[2].cells[0])

    out = '/home/user/kti-support-bot/passport-chaikagrad.docx'
    doc.save(out)
    print(f'Сохранено: {out}')


if __name__ == '__main__':
    make_doc()
