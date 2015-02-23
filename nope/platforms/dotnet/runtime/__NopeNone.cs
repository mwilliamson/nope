internal class __NopeNone
{
    internal static readonly __NopeNone Value = new __NopeNone();
    private __NopeNone() { }
    
    public override string ToString()
    {
        return "None";
    }
    
    public __NopeString __str__()
    {
        return __NopeString.Value(ToString());
    }
}
