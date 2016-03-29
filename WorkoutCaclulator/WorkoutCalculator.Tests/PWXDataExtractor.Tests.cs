using System;
using System.Collections.Generic;
using System.IO;
using System.Xml;
using System.Xml.Serialization;
using BusinessObjects;
using Public;
using Xunit;

namespace WorkoutCalculator.Tests
{
    public class PWCDataExtractorTests
    {
        private pwx _test;

        public XmlNode GetSamplePwxFile(string xmlFileName)
        {
            var doc = new XmlDocument();
            doc.Load(xmlFileName);
            return doc;
        }

        public pwx GetPwxDataFromXml(XmlNode xmlData)
        {
            var stm = new MemoryStream();
            var stw = new StreamWriter(stm);

            stw.Write(xmlData.OuterXml);
            stw.Flush();
            stm.Position = 0;
            var ser = new XmlSerializer(typeof (pwx));
            var pwxObj = ser.Deserialize(stm);
            return pwxObj as pwx;
        }

        public void Initialise()
        {
            if (_test == null)
                _test = GetPwxDataFromXml(GetSamplePwxFile(@"c:\Dev\Autocoach\TestXMLData\TestTurboPowerCyclePWX.xml"));
        }

        [Fact]
        public void TestPWXWorkoutCalculator_cstor()
        {
            Initialise();
            new PWXDataExtractor(_test);
        }

        [Fact]
        public void Test_PWX_Extract_Power()
        {
            Initialise();
            var calc = new PWXDataExtractor(_test);
            var workoutSample = calc.ExtractData();
            Assert.Equal(_test.workout[0].sample.Length, workoutSample.PowerVector.NumberOfSamples);
            Assert.True(workoutSample.PowerVector.HasData);
        }

        [Fact]
        public void Test_2_Workout_PWX_throws_exception()
        {
            var pwx =
                GetPwxDataFromXml(GetSamplePwxFile(@"c:\dev\autocoach\testxmldata\Test2WorkoutTurboPowerCyclePWX.xml"));
            Assert.Throws<ArgumentException>(() => new PWXDataExtractor(pwx));
        }

        //[Fact]
        //public void Test_No_samples_In_Workout_File_returns_Empty_Workout_Samples()
        //{
        //    var pwx =
        //        GetPwxDataFromXml(GetSamplePwxFile(@"c:\dev\autocoach\testxmldata\TestPlannedNotCompletedCycle.xml"));
        //    var dataExtractor = new PWXDataExtractor(pwx);
        //    var woSamples = dataExtractor.ExtractData();
        //    Assert.Equal(0, woSamples.PowerVector.NumberOfSamples);
        //}

        [Fact]
        public void Test_missing_samples_In_Workout_File_returns_Workout_Samples()
        {
            var pwx =
                GetPwxDataFromXml(
                    GetSamplePwxFile(@"c:\dev\autocoach\testxmldata\TestTurboPowerCyclePWXWithMissingSampleData.xml"));
            var dataExtractor = new PWXDataExtractor(pwx);
            var woSamples = dataExtractor.ExtractData();
            Assert.NotEqual(0, woSamples.PowerVector.NumberOfSamples);
        }

        [Fact]
        public void TestAveragePower()
        {
            Initialise();
            var calc = new PWXDataExtractor(_test);
            var workoutSample = calc.ExtractData();
            IAthlete athlete = new Athlete();
            var workoutCalculator = new WorkoutSamplesCalculator(workoutSample,athlete);
            var myPowerAverage = workoutCalculator.GetAveragePower();
            var pwxSummaryPowerAverage = _test.workout[0].summarydata.pwr.avg;
            myPowerAverage = Math.Round(myPowerAverage);
            Assert.Equal(pwxSummaryPowerAverage, myPowerAverage);
        }

        [Fact]
        public void TestNormalizedPower()
        {
            Initialise();
            var calc = new PWXDataExtractor(_test);
            var workoutSample = calc.ExtractData();
            IAthlete athlete = new Athlete();
            var workoutCalculator = new WorkoutSamplesCalculator(workoutSample, athlete);
            var myPowerAverage = workoutCalculator.GetNormalizedPower();
            Assert.Equal(231, myPowerAverage);
        }

        [Fact]
        public void TestIntensityFactor()
        {
            Initialise();
            var calc = new PWXDataExtractor(_test);
            var workoutSample = calc.ExtractData();
            IAthlete athlete = new Athlete();
            athlete.FTBikePower = 240;
            var workoutCalculator = new WorkoutSamplesCalculator(workoutSample,athlete);
            var intensityFactor = workoutCalculator.CalcualteIntensityFactor();
            Assert.Equal(0.96, intensityFactor);
        }

        [Fact]
        public void TestAverageCadence()
        {
            Initialise();
            var calc = new PWXDataExtractor(_test);
            var workoutSample = calc.ExtractData();
            IAthlete athlete = new Athlete();
            var workoutCalculator = new WorkoutSamplesCalculator(workoutSample,athlete);
            var myCadAverage = workoutCalculator.GetAverageCadence();
            var pwxSummaryCadAverage = _test.workout[0].summarydata.cad.avg;
            myCadAverage = Math.Round(myCadAverage);
            Assert.Equal(myCadAverage, 77);
        }

        [Fact]
        public void TestAverageHeartRate()
        {
            Initialise();
            var calc = new PWXDataExtractor(_test);
            var workoutSample = calc.ExtractData();
            IAthlete athlete = new Athlete();
            var workoutCalculator = new WorkoutSamplesCalculator(workoutSample, athlete);
            var myCadAverage = workoutCalculator.GetAverageHeartRate();
            var pwxSummaryAvgHR = _test.workout[0].summarydata.hr.avg;
            myCadAverage = Math.Round(myCadAverage);
            Assert.Equal(pwxSummaryAvgHR, myCadAverage);
        }

        [Fact]
        public void TestAverageSpeed()
        {
            Initialise();
            var calc = new PWXDataExtractor(_test);
            var workoutSample = calc.ExtractData();
            IAthlete athlete = new Athlete();
            var workoutCalculator = new WorkoutSamplesCalculator(workoutSample,athlete);
            var mySpdAverage = workoutCalculator.GetAverageSpeed();
            // double pwxSummaryAvgHR = _test.workout[0].summarydata.spd.avg;
            mySpdAverage = Math.Round(mySpdAverage);
            //Assert.Equal(mySpdAverage, pwxSummaryAvgHR);
        }

        [Fact]
        public void TestPowerBasedTrainingStressScoreCalculation()
        {
            Initialise();
            var calc = new PWXDataExtractor(_test);
            var workoutSample = calc.ExtractData();
            IAthlete athlete = new Athlete();
            var workoutCalculator = new WorkoutSamplesCalculator(workoutSample, athlete);
            var summaryTSS = _test.workout[0].summarydata.tss;
            var roundedTPTSS = Math.Round(summaryTSS, 0);
            var myTSSCalc = workoutCalculator.Calculate_Power_TrainingStressScore(272);
            var roundedMyTSS = Math.Round(myTSSCalc, 0);
            Assert.Equal(roundedTPTSS, roundedMyTSS);
        }

        [Fact]
        public void TestCadenceClassification()
        {
            var pwx =
                GetPwxDataFromXml(
                    GetSamplePwxFile(@"c:\dev\autocoach\testxmldata\TestTurboPowerCyclePZoneClassificationPWX.xml"));
            var dataExtractor = new PWXDataExtractor(pwx);
            var workoutSample = dataExtractor.ExtractData();
            IAthlete athlete = new Athlete();
            var workoutCalculator = new WorkoutSamplesCalculator(workoutSample,athlete);
            var buckets = workoutCalculator.ClassifyWorkoutCadenceRanges();
            Assert.IsType<List<ICadenceRange>>(buckets);
            Assert.Equal(1, buckets[0].QuanityOfSamples);
            Assert.Equal(14, buckets[0].PercentOfTotal);
            Assert.Equal(3, buckets[1].QuanityOfSamples);
            Assert.Equal(43, buckets[1].PercentOfTotal);
            Assert.Equal(0, buckets[2].QuanityOfSamples);
            Assert.Equal(0, buckets[2].PercentOfTotal);
            Assert.Equal(2, buckets[3].QuanityOfSamples);
            Assert.Equal(29, buckets[3].PercentOfTotal);
            Assert.Equal(1, buckets[4].QuanityOfSamples);
            Assert.Equal(14, buckets[4].PercentOfTotal);
        }
        [Fact]
        public void TestSummaryDataExtract_TSS()
        {
            Initialise();
            var calc = new PWXDataExtractor(_test);
            var tss = calc.ExtractSummaryTSS();
            Assert.Equal(110.69, tss);
        }
        [Fact]
        public void TestSummaryDataExtract_Work()
        {
            Initialise();
            var calc = new PWXDataExtractor(_test);
            var tss = calc.ExtractSummaryWork();
            Assert.Equal(3731.6342901494213, tss);
        }
        [Fact]
        public void TestSummaryDataExtract_Duration()
        {
            Initialise();
            var calc = new PWXDataExtractor(_test);
            var tss = calc.ExtractSummaryDuration();
            Assert.Equal(4900.018, tss);
        }

        [Fact]
        public void Test_Workout_Energy_System_Classiication_with_Power()
        {
            Initialise();
            var data = new PWXDataExtractor(_test);
            var samples = data.ExtractData();
            IAthlete athlete = new Athlete();
            var calc = new WorkoutSamplesCalculator(samples, athlete);
            var systems = calc.ClassifyWorkoutPowerRanges(240);
            Assert.IsType<List<IEnergySystemRange>> (systems);
        }

        [Fact]
        public void Test_Workout_Energy_System_Classiication_with_HeartRate()
        {
            Initialise();
            var data = new PWXDataExtractor(_test);
            var samples = data.ExtractData();
            IAthlete athlete = new Athlete();
            var calc = new WorkoutSamplesCalculator(samples, athlete);
            var systems = calc.ClassifyWorkoutEnergeRangesFromHeartRate(160);
            Assert.IsType<List<IEnergySystemRange>>(systems);
        }
        
        [Fact]
        public void CalculateVectorAverage_With_No_Samples_Returns_Zero()
        {
            var samples = new WorkoutSamples(0);
            IAthlete athlete = new Athlete();
            var workoutCalculator = new WorkoutSamplesCalculator(samples, athlete);
            var average = workoutCalculator.GetAverageCadence();
            Assert.Equal(0, average);
        }

        [Fact]
        public void CalculateNormalizedPower_With_No_Samples_Returns_Zero()
        {
            var samples = new WorkoutSamples(0);
            IAthlete athlete = new Athlete();
            var workoutCalculator = new WorkoutSamplesCalculator(samples,athlete);
            var average = workoutCalculator.GetNormalizedPower();
            Assert.Equal(0, average);
        }

        [Fact]
        public void CalculateNormalizedPower_With_Under_30_Samples_Returns_Average()
        {
            //Initialise();
            var samples = new WorkoutSamples(0);
            var vector = new WorkoutSampleVector(2, WorkoutSampleDataType.Power);
            vector.AddPoint(1, 2);
            vector.AddPoint(2, 4);
            IAthlete athlete = new Athlete();
            var workoutCalculator = new WorkoutSamplesCalculator(samples, athlete);
            var average = workoutCalculator.CalculateVectorNormalizedAverage(vector);
            Assert.Equal(3, average);
        }

        [Fact]
        public void CalculatCadenceClassificatoion_Under_2_Samples_returns_()
        {
            var samples = new WorkoutSamples(0);
            var vector = new WorkoutSampleVector(1, WorkoutSampleDataType.Cadence);
            vector.AddPoint(1, 2);
            samples.CadenceVector = vector;
            IAthlete athlete = new Athlete();
            var workoutCalculator = new WorkoutSamplesCalculator(samples, athlete);
            var classification = workoutCalculator.ClassifyWorkoutCadenceRanges();
            Assert.IsType<List<ICadenceRange>>(classification);
        }

        [Fact]
        public void CalculateNonZero_Average_Returns_Average()
        {
            var samples = new WorkoutSamples(0);
            var vector = new WorkoutSampleVector(3, WorkoutSampleDataType.Power);
            vector.AddPoint(1, 2);
            vector.AddPoint(2, 4);
            vector.AddPoint(3, 0);
            IAthlete athlete = new Athlete();
            var workoutCalculator = new WorkoutSamplesCalculator(samples,athlete);
            var average = workoutCalculator.CalculateNonZeroVectorAverage(vector);
            Assert.Equal(3, average);
        }

        [Fact]
        public void CalculateNonZero_Average_With_No_Data_Returns_Zero()
        {
            var samples = new WorkoutSamples(0);
            var vector = new WorkoutSampleVector(3, WorkoutSampleDataType.Power);
            IAthlete athlete = new Athlete();
            var workoutCalculator = new WorkoutSamplesCalculator(samples, athlete);
            var average = workoutCalculator.CalculateNonZeroVectorAverage(vector);
            Assert.Equal(0, average);
        }
    }
}