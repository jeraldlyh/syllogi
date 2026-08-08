from lib.cache import _make_cache_key, cached_function


class TestMakeCacheKey:
    def test_deterministic(self):
        a = _make_cache_key("func", ("a", "b"), {"x": 1})
        b = _make_cache_key("func", ("a", "b"), {"x": 1})

        assert a == b

    def test_different_args_different_keys(self):
        a = _make_cache_key("func", ("a",), {})
        b = _make_cache_key("func", ("b",), {})

        assert a != b

    def test_different_func_name(self):
        a = _make_cache_key("func_a", (), {})
        b = _make_cache_key("func_b", (), {})

        assert a != b

    def test_kwargs_order_independent(self):
        a = _make_cache_key("func", (), {"a": 1, "b": 2})
        b = _make_cache_key("func", (), {"b": 2, "a": 1})

        assert a == b

    def test_returns_hex_string(self):
        key = _make_cache_key("func", (), {})

        assert len(key) == 32


class TestCachedFunction:
    def test_caches_result(self):
        call_count = 0

        @cached_function(ttl=60)
        def expensive_func(x):
            nonlocal call_count
            call_count += 1

            return x * 2

        a = expensive_func(5)
        b = expensive_func(5)

        assert a == 10
        assert b == 10
        assert call_count == 1

    def test_different_args_different_results(self):
        call_count = 0

        @cached_function(ttl=60)
        def func(x):
            nonlocal call_count
            call_count += 1

            return x * 2

        func(1)
        func(2)

        assert call_count == 2

    def test_caches_none_result_not_cached(self):
        call_count = 0

        @cached_function(ttl=60)
        def func(_):
            nonlocal call_count
            call_count += 1


        func(1)
        func(1)

        assert call_count == 2

    def test_caches_empty_list_not_cached(self):
        call_count = 0

        @cached_function(ttl=60)
        def func(_):
            nonlocal call_count
            call_count += 1

            return []

        func(1)
        func(1)
        assert call_count == 2
