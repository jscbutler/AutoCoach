using System;
using System.Globalization;
using System.IO;
using System.Xml.Serialization;
using Public;
using Xunit;

namespace BusinessObjects.Tests
{
    public class TrainingCalendarTests
    {
        public Activity CreateActivity(DateTime startTime)
        {
            return new Activity(SportType.Bike, startTime, TimeSpan.FromHours(1));
        }

        public TrainingCalendarWeek SetupAWeek()
        {
            var aMonday = DateTime.ParseExact("21/03/2016", "dd/MM/yyyy", CultureInfo.InvariantCulture);
            var aDay = DateTime.ParseExact("22/03/2016", "dd/MM/yyyy", CultureInfo.InvariantCulture);

            var day = new TrainingCalendarDay(aDay);
            day.AddActivity(CreateActivity(aDay));
            var week = new TrainingCalendarWeek(aMonday, TrainingPhase.BaseOne, 400, TimeSpan.Zero);
            week.AddDay(day);
            return week;
        }

        [Fact]
        private void TestWeek_Starts_On_Monday()
        {
            var week =
                new TrainingCalendarWeek(DateTime.ParseExact("21/03/2016", "dd/MM/yyyy", CultureInfo.InvariantCulture),
                    TrainingPhase.BaseOne, 0, TimeSpan.Zero);
        }

        [Fact]
        private void TestWeek_Throws_Exception_Start_AnyOtheDay()
        {
            Assert.Throws<ArgumentOutOfRangeException>(
                () =>
                    new TrainingCalendarWeek(
                        DateTime.ParseExact("22/03/2016", "dd/MM/yyyy", CultureInfo.InvariantCulture),
                        TrainingPhase.BaseOne, 0, TimeSpan.Zero));
        }

        [Fact]
        private void Test_Activity_Properites()
        {
            var now = DateTime.Now;
            var activity = CreateActivity(now);
            Assert.Equal(now, activity.StartTime);
            Assert.Equal(TimeSpan.FromHours(1), activity.Duration);
            Assert.Equal(SportType.Bike, activity.SportType);
        }

        [Fact]
        private void TestDaySetup()
        {
            var now = DateTime.Now;
            var day = new TrainingCalendarDay(now);
        }

        [Fact]
        private void TestDayTotalTime()
        {
            var now = DateTime.Now;
            var day = new TrainingCalendarDay(now);
            day.AddActivity(CreateActivity(now));
            day.AddActivity(CreateActivity(now));
            Assert.Equal(TimeSpan.FromHours(2), day.TotalTrainingTime);
        }

        [Fact]
        private void TestDay_Adding_Activity_With_Different_Date_Throws()
        {
            var now = DateTime.Now;
            var day = new TrainingCalendarDay(now + TimeSpan.FromDays(1));
            Assert.Throws<ArgumentOutOfRangeException>(() => day.AddActivity(CreateActivity(now)));
        }

        [Fact]
        private void TestWeeklyActivityTotalTime()
        {
            var week = SetupAWeek();
            var time = week.TotalTrainingTime();
            Assert.Equal(TimeSpan.FromHours(1), time);
        }

        [Fact]
        private void TestAddingDayOutsideWeekThrows()
        {
            var week = SetupAWeek();
            Assert.Throws<ArgumentOutOfRangeException>(() => week.AddDay(new TrainingCalendarDay(DateTime.MinValue)));
        }

        [Fact]
        private void TestXmlSerialization()
        {
            var week = SetupAWeek();
            var serializer = new XmlSerializer(typeof (TrainingCalendarWeek));
            TextWriter writer =
                new StreamWriter(new FileStream(@"c:\dev\AutoCoach\TestXMLData\TrainingCalendarTests.xml",
                    FileMode.Create));
            serializer.Serialize(writer, week);
            writer.Flush();
            writer.Close();
        }

        [Fact]
        private void TestXmlDersialisation()
        {
            var week = SetupAWeek();
            var desers = new XmlSerializer(typeof(TrainingCalendarWeek));
            var reader = new StreamReader(@"c:\dev\AutoCoach\TestXMLData\TrainingCalendarTests.xml");
            var serWeek  = desers.Deserialize(reader);
            Assert.IsType<TrainingCalendarWeek>(serWeek);
            Assert.NotNull(serWeek);
            TrainingCalendarWeek testWeek = (TrainingCalendarWeek) serWeek;
            Assert.Equal(week.WeekHoursTarget, testWeek.WeekHoursTarget);
            Assert.Equal(week.TotalTrainingTime(), testWeek.TotalTrainingTime());
            Assert.Equal(week.FirstDate, testWeek.FirstDate);
            Assert.Equal(week.Phase, testWeek.Phase);
            Assert.Equal(week.WeekTssTarget, testWeek.WeekTssTarget);
        }

    }
}