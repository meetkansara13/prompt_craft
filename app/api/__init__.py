from .routes.key_routes       import bp as key_bp
from .routes.generator_routes import bp as generator_bp
from .routes.optimizer_routes import bp as optimizer_bp
from .routes.history_routes   import bp as history_bp
from .routes.image_routes     import bp as image_bp

__all__ = ["key_bp", "generator_bp", "optimizer_bp", "history_bp", "image_bp"]
