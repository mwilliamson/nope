namespace __Nope
{
    internal class Internals
    {
        internal static readonly object loop_sentinel = new object();
    
        internal static __NopeBoolean op_is(object left, object right)
        {
            return __NopeBoolean.Value(System.Object.ReferenceEquals(left, right));
        }
        
        internal static __NopeBoolean op_is_not(object left, object right)
        {
            return __NopeBoolean.Value(!System.Object.ReferenceEquals(left, right));
        }
    }
}
