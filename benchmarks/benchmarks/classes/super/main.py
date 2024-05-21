class Base:
    def base_action(self):
        pass

class Derived(Base):
    def derived_action(self):
        super().base_action()

instance = Derived()
instance.derived_action()
