using System;

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
    }
}
