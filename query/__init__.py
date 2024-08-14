from .start import router as start_router
from .promo import router as promo_router
from .user import router as user_router
from .distrib import router as distrib_router
from .admin import router as admin_roter
from .review import router as review_router

routers = [start_router, promo_router, user_router, distrib_router, admin_roter, review_router]