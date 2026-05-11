// Fix for DP-ABP-A3F1 — DI: service not registered in correct module
// Bug: cannot resolve service for type 'IInvoiceService'
// Root Cause: InvoiceService registered in BillingModule but [DependsOn] missing

using Volo.Abp.Modularity;

namespace MyApp.Web
{
    [DependsOn(
        typeof(MyAppApplicationModule),
        typeof(BillingModule)        // FIX: was missing — IInvoiceService lives here
    )]
    public class MyAppWebModule : AbpModule
    {
        public override void ConfigureServices(ServiceConfigurationContext context)
        {
            // Module configuration
        }
    }
}
