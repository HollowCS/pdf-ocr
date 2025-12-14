import paddle, sys
print("python:", sys.version.splitlines()[0])
print("paddle version:", getattr(paddle, '__version__', None))
try:
    print("paddle compiled with cuda?:", paddle.is_compiled_with_cuda())
except Exception as e:
    print("paddle.is_compiled_with_cuda() error:", e)
