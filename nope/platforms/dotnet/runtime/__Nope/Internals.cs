using System;
using System.Dynamic;
using System.Collections.Generic;

namespace __Nope
{
    internal class Internals
    {
        internal static readonly object loop_sentinel = new object();
    
        internal static __NopeBoolean op_is(object left, object right)
        {
            return __NopeBoolean.Value(Object.ReferenceEquals(left, right));
        }
        
        internal static __NopeBoolean op_is_not(object left, object right)
        {
            return __NopeBoolean.Value(!Object.ReferenceEquals(left, right));
        }
        
        internal static __NopeException CreateException(dynamic nopeException)
        {
            return new __NopeException(nopeException, Describe(nopeException));
        }
            
        private static string Describe(dynamic nopeException)
        {
            return nopeException.__Type.Name + ": " + nopeException.__str__();
        }

        internal class __NopeException : Exception
        {
            private readonly dynamic _nopeException;
            
            internal __NopeException(dynamic nopeException, string message) : base(message)
            {
                _nopeException = nopeException;
            }
            
            internal dynamic __Value { get { return _nopeException; } }
        }
        
        private static readonly IDictionary<object, dynamic> _moduleCache =
            new Dictionary<object, dynamic>();
        
        internal static dynamic Import(System.Func<dynamic> init)
        {
            lock(_moduleCache) {
                if (!_moduleCache.ContainsKey(init)) {
                    _moduleCache.Add(init, init());
                }
                return _moduleCache[init];
            }
        }
        
        internal static dynamic generator_expression(Func<dynamic, dynamic> func, dynamic iterable)
        {
            var iterator = Builtins.iter(iterable);
            dynamic self = null;
            self = new
            {
                __iter__ = (Func<dynamic>)(() => self),
                __next__ = (Func<dynamic>)(() => func(iterator.__next__()))
            };
            return self;
        }
        
        internal static __NopeList iterator_to_list(dynamic iterator)
        {
            var sentinel = new object();
            var result = new __NopeList();
            dynamic element;
            while ((element = Builtins.next(iterator, sentinel)) != sentinel)
            {
                result.append(element);
            }
            return result;
        }
    }
}
