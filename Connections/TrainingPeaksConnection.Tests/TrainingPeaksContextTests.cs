using System;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace TrainingPeaksConnection.Tests
{
    [TestClass]
    public class TrainingPeaksContextTests
    {
        [TestMethod]
        public void TestMethod1()
        {
            ConnectContext cc = new ConnectContext(null, AccountType.SelfCoachedPremium);
            Assert.AreEqual(cc.accountType, AccountType.SelfCoachedPremium);

        }
        [TestMethod]
        
        public void TestTPSoap()
        {
            TrainingPeaksClient client = new TrainingPeaksClient();
        }
    }
}
