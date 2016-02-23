using System;
using System.Collections.Generic;
using BusinessObjects;
using FakeItEasy;
using Public;
using TrainingPeaksConnection.TrainingPeaksServiceReference;
using Xunit;

namespace TrainingPeaksConnection.Tests
{
    public class TrainingPeaksClientTests
    {
        private const string VALIDUSERNAME = "johndoe11";
        private const string VALIDPASSWORD = "llslsll";
        private const AthleteAccountTypes VALIDACCOUNT = AthleteAccountTypes.CoachedFree;

        private const TrainingPeaksAthleteAccountTypes VALIDINTERNALACCOUNT =
            TrainingPeaksAthleteAccountTypes.CoachedFree;

        private readonly TrainingPeaksClient testFakeClient = null;

        public TrainingPeaksClient SetupFakeTpClient()
        {
            if (testFakeClient != null)
                return testFakeClient;
            //ServiceSoapClient soapClient = new ServiceSoapClient("ServiceSoap");
            var fakeClient = A.Fake<ServiceSoap>();

            var client = new TrainingPeaksClient(fakeClient);
            // TrainingPeaksAthleteAccountTypes tpAccountTypes = TrainingPeaksClient.AccountTypeMapping(VALIDACCOUNT);
            A.CallTo(() => fakeClient.GetAccessibleAthletes(VALIDUSERNAME, VALIDPASSWORD, VALIDACCOUNT))
                .Returns(FakePerson());

            A.CallTo(
                () =>
                    fakeClient.GetWorkoutsForAccessibleAthlete(VALIDUSERNAME, VALIDPASSWORD, A<int>.Ignored,
                        A<DateTime>.Ignored, A<DateTime>.Ignored)).Returns(new[] {FakeWorkout(), FakeWorkout()});
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
            var ret = new PersonBase[1] {fakePerson};
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
            var wo = A.Fake<Workout>();
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
            var athlete = SetupFakeAthlete("", "", TrainingPeaksAthleteAccountTypes.SharedFree);
            var ex = Assert.Throws<Exception>(() => client.GetAthleteData(athlete));
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
        public void TestGetRecentWorkoutIn30Days_Returns_ListOf_2_workout()
        {
            var client = SetupFakeTpClient();
            var athlete = SetupFakeAthlete(VALIDUSERNAME, VALIDPASSWORD, VALIDINTERNALACCOUNT);
            var recentWorkouts = client.GetWorkoutsInLast30Days(athlete);
            Assert.IsType<List<IWorkout>>(recentWorkouts);
            Assert.Equal(recentWorkouts.Count, 2);
        }

        [Fact]
        public void Mapper_for_Cycle_Returns_Cycle_Workout()
        {
            Workout fakeWorkout = A.Fake<Workout>( );
            fakeWorkout.WorkoutTypeDescription = "Cycle";
            var internalWorkout = TrainingPeaksWorkoutMappings.CovertTPWorkoutToInternal(fakeWorkout);
            Assert.IsType<CycleWorkout>(internalWorkout);
        }

        [Fact]
        public void Mapper_for_Swim_Returns_Swim_Workout()
        {
            Workout fakeWorkout = A.Fake<Workout>();
            fakeWorkout.WorkoutTypeDescription = "Swim";
            var internalWorkout = TrainingPeaksWorkoutMappings.CovertTPWorkoutToInternal(fakeWorkout);
            Assert.IsType<SwimWorkout>(internalWorkout);
        }

        [Fact]
        public void Mapper_for_Run_Returns_Run_Workout()
        {
            Workout fakeWorkout = A.Fake<Workout>();
            fakeWorkout.WorkoutTypeDescription = "Run";
            var internalWorkout = TrainingPeaksWorkoutMappings.CovertTPWorkoutToInternal(fakeWorkout);
            Assert.IsType<RunWorkout>(internalWorkout);
        }
        [Fact]
        public void Mapper_for_Custom_Returns_Custom_Workout()
        {
            Workout fakeWorkout = A.Fake<Workout>();
            fakeWorkout.WorkoutTypeDescription = "Custom";
            var internalWorkout = TrainingPeaksWorkoutMappings.CovertTPWorkoutToInternal(fakeWorkout);
            Assert.IsType<CustomWorkout>(internalWorkout);
        }
    }
}