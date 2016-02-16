using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace TrainingPeaksConnection
{
    public class TrainingPeaksClient
    {
        public TrainingPeaksClient()
        {
            TrainingPeaksServiceReference.ServiceSoapClient soapClient = new TrainingPeaksServiceReference.ServiceSoapClient("ServiceSoap");
            var accessibleAthletes = soapClient.GetAccessibleAthletes("jscbutler", "xcelite1", TrainingPeaksServiceReference.AthleteAccountTypes.SelfCoachedPremium);
            foreach (var athlete in accessibleAthletes)
            {
                var name = athlete.FirstName;
            }
        }
    }
}
