internal class __NopeList
{
    internal static __NopeList Values(params dynamic[] values)
    {
        return new __NopeList(new System.Collections.Generic.List<dynamic>(values));
    }
    
    private readonly System.Collections.Generic.IList<dynamic> _values;
    
    internal __NopeList() : this(new System.Collections.Generic.List<dynamic>())
    {
    }
    
    private __NopeList(System.Collections.Generic.IList<dynamic> values)
    {
        _values = values;
    }
    
    internal Iterator __iter__()
    {
        return new Iterator(_values);
    }
    
    internal class Iterator
    {
        private readonly System.Collections.Generic.IList<dynamic> _values;
        private int _nextIndex = 0;
    
        internal Iterator(System.Collections.Generic.IList<dynamic> values)
        {
            _values = values;
        }
        
        internal dynamic __next__()
        {
            if (_nextIndex < _values.Count)
            {
                return _values[_nextIndex++];
            }
            else
            {
                throw __Nope.Internals.CreateException(__Nope.Builtins.StopIteration.__call__());
            }
        }
    }
    
    public __NopeBoolean __bool__()
    {
        return __NopeBoolean.Value(_values.Count > 0);
    }
    
    public dynamic __getitem__(dynamic key)
    {
        if (key is __Nope.Builtins.Slice)
        {
            // TODO: exception on step of 0
            // TODO: implement this in nope
            var result = new __NopeList();
            var step = System.Object.ReferenceEquals(key.step, __NopeNone.Value)
                ? 1 : key.step.__Value;
            
            if (step < 0)
            {
                var start = System.Object.ReferenceEquals(key.start, __NopeNone.Value)
                    ? _values.Count - 1
                    : key.start.__Value;
                var stop = System.Object.ReferenceEquals(key.stop, __NopeNone.Value)
                    ? -1 : key.stop.__Value;
                
                for (var i = start; i > stop; i += step) {
                    result.append(_values[i]);
                }
            }
            else
            {
                var start = System.Object.ReferenceEquals(key.start, __NopeNone.Value)
                    ? 0 : key.start.__Value;
                var stop = System.Object.ReferenceEquals(key.stop, __NopeNone.Value)
                    ? _values.Count : key.stop.__Value;
                
                for (var i = start; i < stop; i += step) {
                    result.append(_values[i]);
                }
            }
            return result;
        }
        else
        {
            var index = key.__Value;
            return index < 0 ? _values[_values.Count + index] : _values[index];
        }
    }
    
    public void __setitem__(__NopeInteger key, dynamic value)
    {
        _values[key.__Value] = value;
    }
    
    public void append(dynamic value)
    {
        _values.Add(value);
    }
    
    public override string ToString()
    {
        return "[" + string.Join(", ", System.Linq.Enumerable.Select(_values, value => value.ToString())) + "]";
    }
    
    public __NopeString __str__()
    {
        return __NopeString.Value(ToString());
    }
}
