import re
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name='render_markdown', is_safe=True)
def render_markdown(text):
    """Convert basic markdown to HTML for chat bubbles. Also strips legacy [user]/[bot] prefixes."""
    if not text:
        return ''
    text = str(text)
    # Strip legacy debug prefixes like "[user] " or "[bot] "
    text = re.sub(r'^\[(user|bot)\]\s*', '', text)
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text, flags=re.DOTALL)
    # Italic
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
    # Inline code
    text = re.sub(r'`(.+?)`', r'<code style="background:rgba(0,0,0,.08);padding:1px 5px;border-radius:4px;font-size:.85em">\1</code>', text)
    # Bullet points — convert "• item" or "- item" lines to proper list items
    lines = text.split('\n')
    result = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('• ') or stripped.startswith('- ') or stripped.startswith('* '):
            item = stripped[2:]
            if not in_list:
                result.append('<ul style="margin:.4em 0 .4em 1.2em;padding:0;list-style:disc">')
                in_list = True
            result.append(f'<li style="margin:.15em 0">{item}</li>')
        else:
            if in_list:
                result.append('</ul>')
                in_list = False
            result.append(line)
    if in_list:
        result.append('</ul>')
    text = '\n'.join(result)
    # Newlines to <br> (but not inside list tags)
    text = re.sub(r'\n(?!<)', '<br>', text)
    return mark_safe(text)
