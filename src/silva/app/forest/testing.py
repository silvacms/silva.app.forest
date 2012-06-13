
from Products.Silva.testing import SilvaLayer

import transaction
import silva.app.forest


class SilvaAppForestLayer(SilvaLayer):
    default_packages = SilvaLayer.default_packages + [
        'silva.app.forest',
        ]

    def _install_application(self, app):
        super(SilvaAppForestLayer, self)._install_application(app)
        app.root.service_extensions.install('silva.app.forest')
        transaction.commit()


FunctionalLayer = SilvaAppForestLayer(silva.app.forest)

