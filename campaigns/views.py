import requests
from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .validators import clean_numbers


@login_required
def create_campaign(request):

    if request.method == "POST":

        name = request.POST.get("name")
        message = request.POST.get("message")
        numbers_text = request.POST.get("numbers")

        # Clean & validate numbers
        result = clean_numbers(numbers_text)
        valid_numbers = result["valid"]

        if not valid_numbers:
            return JsonResponse({
                "status": "error",
                "message": "No valid numbers found."
            })

        success_count = 0
        fail_count = 0
        last_error_message = "All Messages Failed To Send."

        for number in valid_numbers:
            try:
                print("Sending to:", number)

                response = requests.get(
                    f"{settings.WA_BASE_URL}/http-tokenkeyapi.php",
                    params={
                        "authentic-key": settings.WA_API_KEY,
                        "route": 1,
                        "number": number,
                        "message": message
                    },
                    timeout=15
                )

                print("Raw API Response:", response.text)

                api_response = response.json()

                if api_response.get("Status") == "Success":
                    success_count += 1
                else:
                    fail_count += 1

                    description = api_response.get(
                        "Description",
                        "Message Failed"
                    )

                    # 🔥 Custom Friendly Error Mapping
                    if "Authentic Token" in description:
                        last_error_message = "You don't have enough tokens."
                    elif "credit" in description.lower():
                        last_error_message = "You don't have enough tokens."
                    else:
                        last_error_message = description

            except Exception as e:
                print("Exception:", str(e))
                fail_count += 1
                last_error_message = "Server error while sending message."

        print("Success:", success_count, "Fail:", fail_count)

        # Final Response to Frontend
        if success_count > 0:
            return JsonResponse({
                "status": "success",
                "message": f"{success_count} Message(s) Sent Successfully!"
            })
        else:
            return JsonResponse({
                "status": "error",
                "message": last_error_message
            })

    # GET request
    return render(request, "campaigns/create_campaign.html")