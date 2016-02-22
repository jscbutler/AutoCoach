using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.Remoting.Metadata.W3cXsd2001;
using System.Text;
using System.Threading.Tasks;
using BusinessObjects;
using FakeItEasy;
using Public;
using TrainingPeaksConnection.TrainingPeaksServiceReference;
using Xunit;

namespace TrainingPeaksConnection.Tests
{
    public class TrainingPeaksClientTestsXunit
    {
        private TrainingPeaksClient testFakeClient = null;
        private const string VALIDUSERNAME = "johndoe11";
        const string VALIDPASSWORD = "llslsll";
        const AthleteAccountTypes VALIDACCOUNT = AthleteAccountTypes.CoachedFree;
        const TrainingPeaksAthleteAccountTypes VALIDINTERNALACCOUNT = TrainingPeaksAthleteAccountTypes.CoachedFree;

        public TrainingPeaksClient SetupFakeTpClient()
        {
            if (testFakeClient != null)
                return testFakeClient;
            //ServiceSoapClient soapClient = new ServiceSoapClient("ServiceSoap");
            var fakeClient = A.Fake<ServiceSoap>();

            var client = new TrainingPeaksClient(fakeClient);
           // TrainingPeaksAthleteAccountTypes tpAccountTypes = TrainingPeaksClient.AccountTypeMapping(VALIDACCOUNT);
            A.CallTo(() => fakeClient.GetAccessibleAthletes(VALIDUSERNAME,VALIDPASSWORD ,VALIDACCOUNT))
                .Returns(FakePerson());

            A.CallTo(
                () =>
                    fakeClient.GetWorkoutsForAccessibleAthlete(VALIDUSERNAME, VALIDPASSWORD, A<int>.Ignored,
                        A<DateTime>.Ignored, A<DateTime>.Ignored)).Returns( new Workout[] {FakeWorkout(), FakeWorkout()});
            return client;
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
            var ret = new PersonBase[1] { fakePerson };
            return ret;
        }

        public Athlete SetupFakeAthlete(string username, string password, TrainingPeaksAthleteAccountTypes accountType)
        {
            var athlete = new Athlete
            {
                TPData = new TrainingPeaksAthleteData
                {
                    LoginName = username,
                    LoginPassword = password,
                    AccountType = accountType
                }
            };

            return athlete;
        }

        public Workout FakeWorkout()
        {
            Workout wo = A.Fake<Workout>();
            return wo;
        }


        [Fact]
        public void TestTrainingPeaskConstructor()
        {
            var client = SetupFakeTpClient();
            Assert.IsType<TrainingPeaksClient>(client);
            
        }

        [Fact]
        public void TestGetAthlete_ThrowsException_with_Zero_Athletes()
        {
            var client = SetupFakeTpClient();
            var athlete = SetupFakeAthlete("","",TrainingPeaksAthleteAccountTypes.SharedFree);
            Exception ex = Assert.Throws<Exception>(() => client.GetAthleteData(athlete));

         
        }
        [Fact]
        public void TestGetAthlete_Returns_Person_And_Populates_Name_ID()
        {
            var client = SetupFakeTpClient();
            var athlete = SetupFakeAthlete(VALIDUSERNAME, VALIDPASSWORD, VALIDINTERNALACCOUNT);
            client.GetAthleteData(athlete);
            Assert.NotNull(athlete.TPData.AthleteName);
            Assert.Equal(athlete.TPData.PersonID, 12345);
        }

        [Fact]
        public void TestGetLastWorkoutIn30Days_Returns_one_workout()
        {
            var client = SetupFakeTpClient();
            var athlete = SetupFakeAthlete(VALIDUSERNAME, VALIDPASSWORD, VALIDINTERNALACCOUNT);
            var workout = client.GetLastWorkoutIn30Days(athlete);
            Assert.IsAssignableFrom<IWorkout>(workout);
        }

        [Fact]
        public void TestGetRecentWorkoutIn30Days_Returns_one_workout()
        {
            var client = SetupFakeTpClient();
            var athlete = SetupFakeAthlete(VALIDUSERNAME, VALIDPASSWORD, VALIDINTERNALACCOUNT);
            var recentWorkouts = client.GetRecentWorkouts(athlete);
            Assert.IsType<List<IWorkout>>(recentWorkouts);
        }

    }
}
