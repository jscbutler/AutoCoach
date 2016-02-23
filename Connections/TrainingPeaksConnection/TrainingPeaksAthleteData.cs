using Public;

namespace TrainingPeaksConnection
{
    public class TrainingPeaksAthleteData : ITrainingPeaksAthleteData
    {
        public TrainingPeaksAthleteAccountTypes AccountType { get; set; }
        public string AthleteName { get; set; }
        public string LoginName { get; set; }
        public string LoginPassword { get; set; }
        public int PersonID { get; set; }
    }
}