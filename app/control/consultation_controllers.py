from datetime import datetime, timedelta
from app.entity.consultation_slot import ConsultationSlot

class SetAvailabilityController:
    def __init__(self):
        self.errors = []
        self.slot = None

    def get_availability_calendar(self, designer_id):
        return ConsultationSlot.get_slots_by_designer(designer_id)

    def set_availability(self, designer, date_str, start_time_str, duration_hours=1):
        self.errors = []

        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            start_time_obj = datetime.strptime(start_time_str, "%H:%M").time()
            
            slot_start_dt = datetime.combine(date_obj, start_time_obj)
            # Automatically calculate end time based on selected duration (e.g., 1 or 2 hours)
            slot_end_dt = slot_start_dt + timedelta(hours=int(duration_hours))
            
            end_time_str = slot_end_dt.strftime("%H:%M")
            now = datetime.now()

            # Future validation check
            if slot_start_dt <= now:
                self.errors.append("The slot start time must be in the future.")

            # Overlap check against existing slots
            existing_slots = ConsultationSlot.get_slots_by_designer(designer.user_id)
            for s in existing_slots:
                if str(s.date) == date_str:
                    existing_start = datetime.strptime(s.startTime, "%H:%M").time()
                    existing_end = datetime.strptime(s.endTime, "%H:%M").time()
                    if not (slot_end_dt.time() <= existing_start or start_time_obj >= existing_end):
                        self.errors.append("This time slot overlaps with an existing slot.")
                        break

            if self.errors:
                return False

            self.slot = designer.setAvailability(date_str, start_time_str, end_time_str)
            if not self.slot:
                self.errors = ["Could not save the consultation slot."]
                return False

            return True

        except (ValueError, TypeError):
            self.errors = ["Invalid date or time format provided."]
            return False