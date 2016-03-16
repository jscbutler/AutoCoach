using System;
using BusinessObjects;

namespace WorkoutCalculator
{
    public class PWXDataExtractor
    {
        private readonly pwx _file;
        private readonly int numSamples;

        public PWXDataExtractor(pwx data)
        {
            _file = data;
            if (data.workout.Length > 1)
                throw new ArgumentException("No support for more than 1 workout per PWX file");
            if ((_file != null)  && (_file.workout.Length >0) && (_file.workout[0].sample !=null))
                numSamples = _file.workout[0].sample.Length;
        }

        public WorkoutSamples ExtractData()
        {
            if (numSamples <= 0)
            {
                return new WorkoutSamples(0);
            }
            var woSamples = new WorkoutSamples(numSamples);
            foreach (var sample in _file.workout[0].sample)
            {
                if (sample.pwrSpecified)
                    woSamples.AddPoint(sample.timeoffset, sample.pwr, WorkoutSampleDataType.Power);
                else
                    woSamples.AddPoint(sample.timeoffset, -1, WorkoutSampleDataType.Power);
                if (sample.cadSpecified)
                    woSamples.AddPoint(sample.timeoffset, sample.cad, WorkoutSampleDataType.Cadence);
                else
                    woSamples.AddPoint(sample.timeoffset, -1, WorkoutSampleDataType.Cadence);
                if(sample.hrSpecified)
                    woSamples.AddPoint(sample.timeoffset, sample.hr, WorkoutSampleDataType.HeartRate);
                else
                    woSamples.AddPoint(sample.timeoffset, -1, WorkoutSampleDataType.HeartRate);
                if(sample.spdSpecified)
                    woSamples.AddPoint(sample.timeoffset, sample.hr, WorkoutSampleDataType.Speed);
                else
                    woSamples.AddPoint(sample.timeoffset, -1, WorkoutSampleDataType.Speed);
                
            }
            woSamples.SummaryTrainingStressScore = ExtractSummaryTSS();
            woSamples.SummaryDuration = ExtractSummaryDuration();
            woSamples.SummaryWork = ExtractSummaryWork();
            return woSamples;
        }

        public double ExtractSummaryTSS()
        {
            return _file.workout[0].summarydata.tss;
        }
        public double ExtractSummaryWork()
        {
            return _file.workout[0].summarydata.work;
        }
        public double ExtractSummaryDuration()
        {
            return _file.workout[0].summarydata.duration;
        }

    }
}