using System;
using BusinessObjects;
using FakeItEasy;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Public;
using TrainingPeaksConnection.TrainingPeaksServiceReference;

namespace TrainingPeaksConnection.Tests
{
    [TestClass]
    public class TrainingPeaksClientTests
    {
        public TrainingPeaksClient SetupFakeTpClient()
        {
            //ServiceSoapClient soapClient = new ServiceSoapClient("ServiceSoap");
            var fakeClient = A.Fake<ServiceSoap>();

            var client = new TrainingPeaksClient(fakeClient);
            A.CallTo(() => fakeClient.GetAccessibleAthletes("", "", AthleteAccountTypes.CoachedFree))
                .Returns(FakePerson());
            return client;
        }


        [TestMethod]
        public void TestTrainingPeaskConstructorp()
        {
            var client = SetupFakeTpClient();
            Assert.IsInstanceOfType(client, typeof (TrainingPeaksClient));
        }

        [TestMethod]
        public void TestGetAthlete_ThrowsException_with_Zero_Athletes()
        {
            var client = SetupFakeTpClient();
            var athlete = SetupAthlete();
            Action action = () => client.GetAthleteData(athlete);
            // Add exception checks with NUnit or such.
            //A.CallTo(() => client.GetAthleteData(athlete)).

            ;
        }

        [TestMethod]
        public void TestGetAthlete_Returns_Person_And_Populates_Name_ID()
        {
            var client = SetupFakeTpClient();
            var athlete = SetupAthlete();


            client.GetAthleteData(athlete);

            Assert.IsNotNull(athlete.TPData.AthleteName);
            Assert.AreEqual(athlete.TPData.PersonID, 12345);
        }

        [TestMethod]
        public void TPAccountTypeMap()
        {
            foreach (
                TrainingPeaksAthleteAccountTypes trainingPeaksAthleteAccountType in
                    Enum.GetValues(typeof (TrainingPeaksAthleteAccountTypes)))
            {
                Assert.AreEqual((int) TrainingPeaksClient.AccountTypeMapping(trainingPeaksAthleteAccountType),
                    (int) trainingPeaksAthleteAccountType);
            }
        }

        public PersonBase[] FakePerson()
        {
            var fakePerson = A.Fake<PersonBase>();
            fakePerson.Age = 33;
            fakePerson.AthleteTypeValue = AthleteType.Triathlete;
            fakePerson.FirstName = "John";
            fakePerson.LastName = "Doe";
            fakePerson.Username = "jdoe";
            fakePerson.PersonId = 12345;
            var ret = new PersonBase[1] {fakePerson};
            return ret;
        }

        public Athlete SetupAthlete()
        {
            var athlete = new Athlete
            {
                TPData = new TrainingPeaksAthleteData
                {
                    LoginName = "",
                    LoginPassword = "",
                    AccountType = TrainingPeaksAthleteAccountTypes.CoachedFree
                }
            };

            return athlete;
        }
    }
}