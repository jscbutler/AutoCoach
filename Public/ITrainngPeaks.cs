namespace Public
{
    public interface ITrainingPeaksAthleteData
    {
        string LoginName { get; set; }
        string LoginPassword { get; set; }
        TrainingPeaksAthleteAccountTypes AccountType { get; set; }
        int PersonID { get; set; }
        string AthleteName { get; set; }
    }


    public enum TrainingPeaksAthleteAccountTypes
    {
        /// <remarks />
        CoachedPremium = 1,

        /// <remarks />
        SelfCoachedPremium = 2,

        /// <remarks />
        SharedSelfCoachedPremium = 4,

        /// <remarks />
        SharedCoachedPremium = 8,

        /// <remarks />
        CoachedFree = 16,

        /// <remarks />
        SharedFree = 32,

        /// <remarks />
        Plan = 64
    }
}