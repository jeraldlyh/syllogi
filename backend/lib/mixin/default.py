class DefaultAttrMixin:
    DEFAULTS: dict = {}

    @classmethod
    def get_default(self) -> dict:
        return dict(self.DEFAULTS)
