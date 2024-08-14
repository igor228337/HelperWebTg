from .start import router as start_router
from .user import routers as user_router
from .admin import routers as admin_router
from .review import routers as review_router

routers = [start_router]
routers.extend(admin_router)
routers.extend(review_router)
routers.extend(user_router)