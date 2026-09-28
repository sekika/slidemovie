__all__ = ["Movie"]


def __getattr__(name):
    """Load the build implementation only when it is actually needed.

    This lets lightweight CLI operations such as ``slidemovie --help`` work
    without importing TTS providers or checking their platform dependencies.
    """
    if name == "Movie":
        from .core import Movie
        return Movie
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
