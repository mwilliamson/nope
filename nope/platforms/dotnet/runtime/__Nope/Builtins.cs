using System;

namespace __Nope
{
    internal class Builtins
    {
        internal static readonly dynamic Exception = new
        {
            Name = "Exception",
            __BaseClasses = new dynamic[] {},
            __call__ = (System.Func<dynamic, dynamic>)(message => new
            {
                __Type = Exception,
                __str__ = (Func<dynamic>)(() => message)
            })
        };
        
        internal static readonly dynamic AssertionError = new
        {
            Name = "AssertionError",
            __BaseClasses = new dynamic[] {Exception},
            __call__ = (System.Func<dynamic, dynamic>)(message => new
            {
                __Type = AssertionError,
                __str__ = (Func<dynamic>)(() => message)
            })
        };
    
        internal static __NopeBoolean @bool(dynamic value)
        {
            if (value.GetType().GetMethod("__bool__") != null)
            {
                return value.__bool__();
            }
            else
            {
                return __NopeBoolean.False;
            }
        }
        
        internal static dynamic next(dynamic iterator, dynamic stopValue)
        {
            try
            {
                return iterator.__next__();
            }
            catch (StopIteration)
            {
                return stopValue;
            }
        }
        
        internal static dynamic iter(dynamic iterable)
        {
            return iterable.__iter__();
        }
        
        internal static readonly dynamic str = new
        {
            __call__ = (Func<dynamic, __NopeString>)(value => value.__str__())
        };
        
        internal static __NopeBoolean isinstance(dynamic obj, dynamic type)
        {
            var isinstance = obj.__Type == type ||
                System.Linq.Enumerable.Any(obj.__Type.__BaseClasses, (Func<dynamic, bool>)(baseClass => baseClass == type));
            return __NopeBoolean.Value(isinstance);
        }
        
        internal class StopIteration : System.Exception
        {
        }
        
        internal static RangeIterator range(__NopeInteger start, __NopeInteger end)
        {
            return new RangeIterator(start.__Value, end.__Value);
        }
        
        internal class RangeIterator
        {
            private int _index;
            private readonly int _end;
        
            internal RangeIterator(int start, int end)
            {
                _index = start;
                _end = end;
            }
            
            internal RangeIterator __iter__()
            {
                return this;
            }
            
            internal __NopeInteger __next__()
            {
                if (_index < _end)
                {
                    return __NopeInteger.Value(_index++);
                }
                else
                {
                    throw new StopIteration();
                }
            }
        }
        
        internal static Slice slice(dynamic start, dynamic stop, dynamic step)
        {
            return new Slice(start, stop, step);
        }
        
        internal class Slice
        {
            private readonly dynamic _start;
            private readonly dynamic _stop;
            private readonly dynamic _step;
            
            internal Slice(dynamic start, dynamic stop, dynamic step)
            {
                _start = start;
                _stop = stop;
                _step = step;
            }
            
            internal dynamic start { get { return _start; } }
            internal dynamic stop { get { return _stop; } }
            internal dynamic step { get { return _step; } }
        }
    }
}
