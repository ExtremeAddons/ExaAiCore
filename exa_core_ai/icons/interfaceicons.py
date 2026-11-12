


class ExaCoreAiIcons:
    custom_icons = None
    custom_icons_prop = []

def enum_custom_icons(self, context):

    if ExaCoreAiIcons.custom_icons_prop:
        return ExaCoreAiIcons.custom_icons_prop

    for idx, (name, thumb) in enumerate(ExaCoreAiIcons.custom_icons.items()):
        ExaCoreAiIcons.custom_icons_prop.append((name, name, "", thumb.icon_id, idx))

    return ExaCoreAiIcons.custom_icons_prop


def get_icon(string):
    return ExaCoreAiIcons.custom_icons[string+".png"].icon_id


