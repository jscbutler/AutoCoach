using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Public;
namespace TrainingPeaksConnection
{

    public enum AccountType
    {
        CoachedPremium,
        SelfCoachedPremium,
        SharedSelfCoachedPremium,
        SharedCoachedPremium,
        CoachedFree,
        SharedFree,
        Plan
    }
    public class ConnectContext
    {
        public AccountType accountType
        {
            get;
        }
       
        public ConnectContext (IAthlete athlete, AccountType accountType)
        {
            
            this.accountType = accountType;
        }
    }
}
